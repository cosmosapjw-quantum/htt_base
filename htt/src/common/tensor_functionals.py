"""Typed tensor-functional evaluation over the canonical joint state.

This module extends the PR-254 anchor authority; it does not create another
anchor hierarchy.  A functional result keeps six questions separate:

* the evaluated value;
* whether the state lies in the declared domain;
* the codomain shape and O(3) type;
* whether the existing anchor is usable;
* which downstream diagnostic operations are admissible; and
* the PR-254 gauge/margin stress report.

Missing channels never become zeros.  The contracts are diagnostic-only and
carry no likelihood, posterior, evidence, native-solver, geometry-detection,
or family-identification semantics.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Integral, Real
from typing import Mapping, Sequence

import numpy as np

from common.anchor_geometry import (
    AnchorAvailability,
    AnchorBlockSpec,
    AnchorBodySpec,
    AnchorFamily,
    AnchorFamilyKind,
    AnchorGaugeInterval,
    AnchorGaugeStatus,
    AnchorGeometryError,
    AnchorMarginReport,
    AnchorVector,
    PolytopeHalfspace,
    build_anchor_margin_report,
    evaluate_anchor_gauge,
)
from common.joint_anisotropy_state import (
    JointAnisotropyState,
    JointAnisotropyStateError,
    MissingComponent,
)
from common.orbit_nonlinearity import stf5_to_matrix


class TensorFunctionalError(ValueError):
    """Raised when a functional contract is malformed or internally drifts."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class TensorFunctionalOperator(_StringEnum):
    SIGMA_STF5 = "SIGMA_STF5"
    OMEGA_AXIAL3 = "OMEGA_AXIAL3"
    ACCELERATION_POLAR3 = "ACCELERATION_POLAR3"
    BETA_RM_POLAR3 = "BETA_RM_POLAR3"
    BETA_MO_POLAR3 = "BETA_MO_POLAR3"
    BETA_RO_POLAR3 = "BETA_RO_POLAR3"
    DELTA_OMEGA_K = "DELTA_OMEGA_K"
    TR_SIGMA2 = "TR_SIGMA2"
    TR_SIGMA3 = "TR_SIGMA3"
    OMEGA2 = "OMEGA2"
    BETA_RM2 = "BETA_RM2"
    BETA_RM_DOT_OMEGA = "BETA_RM_DOT_OMEGA"
    BETA_RM_SIGMA_BETA_RM = "BETA_RM_SIGMA_BETA_RM"


class FunctionalO3Type(_StringEnum):
    SCALAR = "SCALAR"
    PSEUDOSCALAR = "PSEUDOSCALAR"
    POLAR_VECTOR = "POLAR_VECTOR"
    AXIAL_VECTOR = "AXIAL_VECTOR"
    STF2_TENSOR = "STF2_TENSOR"


class FunctionalSignClass(_StringEnum):
    SIGN_DEFINITE = "SIGN_DEFINITE"
    SIGNED = "SIGNED"
    EQUIVARIANT = "EQUIVARIANT"


class FunctionalDomainStatus(_StringEnum):
    ADMISSIBLE = "ADMISSIBLE"
    METADATA_MISMATCH = "METADATA_MISMATCH"
    MISSING_COMPONENT = "MISSING_COMPONENT"
    FORBIDDEN_DOMAIN = "FORBIDDEN_DOMAIN"


class FunctionalAnchorStatus(_StringEnum):
    NOT_REQUESTED = "NOT_REQUESTED"
    DEFINED = "DEFINED"
    CONDITIONAL = "CONDITIONAL"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    OPTIMIZER_REQUIRED = "OPTIMIZER_REQUIRED"
    RANK_DEFICIENT = "RANK_DEFICIENT"
    NON_COMPACT_SUPPORT = "NON_COMPACT_SUPPORT"


class FunctionalAdmissibilityStatus(_StringEnum):
    ADMISSIBLE = "ADMISSIBLE"
    ABSTAIN = "ABSTAIN"


class FunctionalStressStatus(_StringEnum):
    DEFINED = "DEFINED"
    CONDITIONAL = "CONDITIONAL"
    UNAVAILABLE = "UNAVAILABLE"


FUNCTIONAL_CLAIM_CEILING = "diagnostic_only"
FUNCTIONAL_ALLOWED_USE = (
    "formal tensor-functional evaluation",
    "typed premise-anchor stress diagnostic",
    "O(3) covariance and parity regression",
)
FUNCTIONAL_FORBIDDEN_USE = (
    "likelihood, posterior, Bayes factor, or evidence term",
    "native solver validation or native morphology atlas",
    "geometry detection or Bianchi family identification",
)
FUNCTIONAL_SOURCE_SCHEMA = "HTT_JOINT_ANISOTROPY_STATE_V1"
FUNCTIONAL_INPUT_REPRESENTATION = (
    "KINEMATICS_PLUS_VELOCITY_PLUS_PARTIAL_GEOMETRY_V1"
)
_SPEC_TOKEN = object()
_RESULT_TOKEN = object()


@dataclass(frozen=True)
class _OperatorContract:
    output_shape: tuple[int, ...]
    coordinate_suffixes: tuple[str, ...]
    tensor_degree: int
    o3_type: FunctionalO3Type
    sign_class: FunctionalSignClass
    required_components: tuple[str, ...]


_OPERATORS: Mapping[TensorFunctionalOperator, _OperatorContract] = {
    TensorFunctionalOperator.SIGMA_STF5: _OperatorContract(
        (5,),
        ("xx", "yy", "xy", "xz", "yz"),
        1,
        FunctionalO3Type.STF2_TENSOR,
        FunctionalSignClass.EQUIVARIANT,
        ("sigma_stf5",),
    ),
    TensorFunctionalOperator.OMEGA_AXIAL3: _OperatorContract(
        (3,),
        ("x", "y", "z"),
        1,
        FunctionalO3Type.AXIAL_VECTOR,
        FunctionalSignClass.EQUIVARIANT,
        ("omega_axial3",),
    ),
    TensorFunctionalOperator.ACCELERATION_POLAR3: _OperatorContract(
        (3,),
        ("x", "y", "z"),
        1,
        FunctionalO3Type.POLAR_VECTOR,
        FunctionalSignClass.EQUIVARIANT,
        ("acceleration_polar3",),
    ),
    TensorFunctionalOperator.BETA_RM_POLAR3: _OperatorContract(
        (3,),
        ("x", "y", "z"),
        1,
        FunctionalO3Type.POLAR_VECTOR,
        FunctionalSignClass.EQUIVARIANT,
        ("beta_RM",),
    ),
    TensorFunctionalOperator.BETA_MO_POLAR3: _OperatorContract(
        (3,),
        ("x", "y", "z"),
        1,
        FunctionalO3Type.POLAR_VECTOR,
        FunctionalSignClass.EQUIVARIANT,
        ("beta_MO",),
    ),
    TensorFunctionalOperator.BETA_RO_POLAR3: _OperatorContract(
        (3,),
        ("x", "y", "z"),
        1,
        FunctionalO3Type.POLAR_VECTOR,
        FunctionalSignClass.EQUIVARIANT,
        ("beta_RO",),
    ),
    TensorFunctionalOperator.DELTA_OMEGA_K: _OperatorContract(
        (1,),
        ("value",),
        1,
        FunctionalO3Type.SCALAR,
        FunctionalSignClass.SIGNED,
        ("delta_omega_k",),
    ),
    TensorFunctionalOperator.TR_SIGMA2: _OperatorContract(
        (1,),
        ("value",),
        2,
        FunctionalO3Type.SCALAR,
        FunctionalSignClass.SIGN_DEFINITE,
        ("sigma_stf5",),
    ),
    TensorFunctionalOperator.TR_SIGMA3: _OperatorContract(
        (1,),
        ("value",),
        3,
        FunctionalO3Type.SCALAR,
        FunctionalSignClass.SIGNED,
        ("sigma_stf5",),
    ),
    TensorFunctionalOperator.OMEGA2: _OperatorContract(
        (1,),
        ("value",),
        2,
        FunctionalO3Type.SCALAR,
        FunctionalSignClass.SIGN_DEFINITE,
        ("omega_axial3",),
    ),
    TensorFunctionalOperator.BETA_RM2: _OperatorContract(
        (1,),
        ("value",),
        2,
        FunctionalO3Type.SCALAR,
        FunctionalSignClass.SIGN_DEFINITE,
        ("beta_RM",),
    ),
    TensorFunctionalOperator.BETA_RM_DOT_OMEGA: _OperatorContract(
        (1,),
        ("value",),
        2,
        FunctionalO3Type.PSEUDOSCALAR,
        FunctionalSignClass.SIGNED,
        ("beta_RM", "omega_axial3"),
    ),
    TensorFunctionalOperator.BETA_RM_SIGMA_BETA_RM: _OperatorContract(
        (1,),
        ("value",),
        3,
        FunctionalO3Type.SCALAR,
        FunctionalSignClass.SIGNED,
        ("beta_RM", "sigma_stf5"),
    ),
}


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise TensorFunctionalError(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TensorFunctionalError(f"{name} must be a sequence of text")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise TensorFunctionalError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise TensorFunctionalError(f"{name} must not contain duplicates")
    return out


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise TensorFunctionalError(f"{name} must be an integer")
    out = int(value)
    if out < minimum:
        raise TensorFunctionalError(f"{name} must be at least {minimum}")
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise TensorFunctionalError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise TensorFunctionalError(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise TensorFunctionalError(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise TensorFunctionalError(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise TensorFunctionalError(f"{name} must be finite")
    return out


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _enum(value: object, enum_type: type[_StringEnum], name: str) -> _StringEnum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        raise TensorFunctionalError(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        ) from exc


@dataclass(frozen=True)
class TensorFunctionalSpec:
    """Factory-built identity for one declared state functional."""

    functional_id: str
    operator: TensorFunctionalOperator
    output_shape: tuple[int, ...]
    coordinate_labels: tuple[str, ...]
    tensor_degree: int
    o3_type: FunctionalO3Type
    sign_class: FunctionalSignClass
    required_components: tuple[str, ...]
    frame: str
    congruence: str
    epoch_window: str
    averaging_scale: str
    normalization: str
    perturbative_order: str
    branch: str
    anchor_id: str | None
    source_state_schema: str = FUNCTIONAL_SOURCE_SCHEMA
    input_representation: str = FUNCTIONAL_INPUT_REPRESENTATION
    claim_ceiling: str = FUNCTIONAL_CLAIM_CEILING
    allowed_use: tuple[str, ...] = FUNCTIONAL_ALLOWED_USE
    forbidden_use: tuple[str, ...] = FUNCTIONAL_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SPEC_TOKEN:
            raise TensorFunctionalError(
                "TensorFunctionalSpec must be created by "
                "build_tensor_functional_spec or from_payload"
            )
        _text(self.functional_id, "functional_id")
        if type(self.operator) is not TensorFunctionalOperator:
            raise TensorFunctionalError(
                "operator must be an exact TensorFunctionalOperator"
            )
        contract = _OPERATORS[self.operator]
        shape = tuple(
            _integer(value, "output_shape", minimum=1)
            for value in self.output_shape
        )
        if shape != contract.output_shape:
            raise TensorFunctionalError(
                "output_shape does not match the registered operator"
            )
        labels = _texts(self.coordinate_labels, "coordinate_labels")
        if len(labels) != math.prod(shape):
            raise TensorFunctionalError(
                "coordinate_labels must cover the flattened codomain"
            )
        if self.tensor_degree != contract.tensor_degree:
            raise TensorFunctionalError(
                "tensor_degree does not match the registered operator"
            )
        if self.o3_type is not contract.o3_type:
            raise TensorFunctionalError(
                "o3_type does not match the registered operator"
            )
        if self.sign_class is not contract.sign_class:
            raise TensorFunctionalError(
                "sign_class does not match the registered operator"
            )
        if tuple(self.required_components) != contract.required_components:
            raise TensorFunctionalError(
                "required_components do not match the registered operator"
            )
        for name in (
            "frame",
            "congruence",
            "epoch_window",
            "averaging_scale",
            "normalization",
            "perturbative_order",
            "branch",
        ):
            _text(getattr(self, name), name)
        if self.anchor_id is not None:
            _text(self.anchor_id, "anchor_id")
        if self.source_state_schema != FUNCTIONAL_SOURCE_SCHEMA:
            raise TensorFunctionalError("source_state_schema drifted")
        if self.input_representation != FUNCTIONAL_INPUT_REPRESENTATION:
            raise TensorFunctionalError("input_representation drifted")
        if self.claim_ceiling != FUNCTIONAL_CLAIM_CEILING:
            raise TensorFunctionalError("functional claim ceiling drifted")
        if tuple(self.allowed_use) != FUNCTIONAL_ALLOWED_USE:
            raise TensorFunctionalError("functional allowed-use lane drifted")
        if tuple(self.forbidden_use) != FUNCTIONAL_FORBIDDEN_USE:
            raise TensorFunctionalError("functional forbidden-use lane drifted")
        object.__setattr__(self, "output_shape", shape)
        object.__setattr__(self, "coordinate_labels", labels)

    @property
    def spec_id(self) -> str:
        return _sha256_payload(self.to_payload())

    def to_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "anchor_id": self.anchor_id,
            "averaging_scale": self.averaging_scale,
            "branch": self.branch,
            "claim_ceiling": self.claim_ceiling,
            "congruence": self.congruence,
            "coordinate_labels": list(self.coordinate_labels),
            "epoch_window": self.epoch_window,
            "forbidden_use": list(self.forbidden_use),
            "frame": self.frame,
            "functional_id": self.functional_id,
            "input_representation": self.input_representation,
            "normalization": self.normalization,
            "o3_type": self.o3_type.value,
            "operator": self.operator.value,
            "output_shape": list(self.output_shape),
            "perturbative_order": self.perturbative_order,
            "required_components": list(self.required_components),
            "schema": "HTT_TENSOR_FUNCTIONAL_SPEC_V1",
            "sign_class": self.sign_class.value,
            "source_state_schema": self.source_state_schema,
            "tensor_degree": self.tensor_degree,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "TensorFunctionalSpec":
        if not isinstance(payload, Mapping):
            raise TensorFunctionalError("functional spec payload must be a mapping")
        expected = {
            "allowed_use",
            "anchor_id",
            "averaging_scale",
            "branch",
            "claim_ceiling",
            "congruence",
            "coordinate_labels",
            "epoch_window",
            "forbidden_use",
            "frame",
            "functional_id",
            "input_representation",
            "normalization",
            "o3_type",
            "operator",
            "output_shape",
            "perturbative_order",
            "required_components",
            "schema",
            "sign_class",
            "source_state_schema",
            "tensor_degree",
        }
        if set(payload) != expected:
            raise TensorFunctionalError("functional spec payload keys mismatch")
        if payload["schema"] != "HTT_TENSOR_FUNCTIONAL_SPEC_V1":
            raise TensorFunctionalError("unknown functional spec schema")
        operator = _enum(
            payload["operator"], TensorFunctionalOperator, "operator"
        )
        return cls(
            functional_id=payload["functional_id"],  # type: ignore[arg-type]
            operator=operator,  # type: ignore[arg-type]
            output_shape=tuple(payload["output_shape"]),  # type: ignore[arg-type]
            coordinate_labels=tuple(payload["coordinate_labels"]),  # type: ignore[arg-type]
            tensor_degree=payload["tensor_degree"],  # type: ignore[arg-type]
            o3_type=_enum(payload["o3_type"], FunctionalO3Type, "o3_type"),  # type: ignore[arg-type]
            sign_class=_enum(
                payload["sign_class"], FunctionalSignClass, "sign_class"
            ),  # type: ignore[arg-type]
            required_components=tuple(payload["required_components"]),  # type: ignore[arg-type]
            frame=payload["frame"],  # type: ignore[arg-type]
            congruence=payload["congruence"],  # type: ignore[arg-type]
            epoch_window=payload["epoch_window"],  # type: ignore[arg-type]
            averaging_scale=payload["averaging_scale"],  # type: ignore[arg-type]
            normalization=payload["normalization"],  # type: ignore[arg-type]
            perturbative_order=payload["perturbative_order"],  # type: ignore[arg-type]
            branch=payload["branch"],  # type: ignore[arg-type]
            anchor_id=payload["anchor_id"],  # type: ignore[arg-type]
            source_state_schema=payload["source_state_schema"],  # type: ignore[arg-type]
            input_representation=payload["input_representation"],  # type: ignore[arg-type]
            claim_ceiling=payload["claim_ceiling"],  # type: ignore[arg-type]
            allowed_use=tuple(payload["allowed_use"]),  # type: ignore[arg-type]
            forbidden_use=tuple(payload["forbidden_use"]),  # type: ignore[arg-type]
            _construction_token=_SPEC_TOKEN,
        )


def build_tensor_functional_spec(
    *,
    functional_id: str,
    operator: TensorFunctionalOperator | str,
    frame: str,
    congruence: str,
    epoch_window: str,
    averaging_scale: str,
    normalization: str,
    perturbative_order: str,
    branch: str,
    anchor_id: str | None = None,
) -> TensorFunctionalSpec:
    """Build a functional identity from the closed operator registry."""

    resolved = _enum(operator, TensorFunctionalOperator, "operator")
    contract = _OPERATORS[resolved]  # type: ignore[index]
    labels = tuple(
        f"{functional_id}:{suffix}" for suffix in contract.coordinate_suffixes
    )
    return TensorFunctionalSpec(
        functional_id=functional_id,
        operator=resolved,  # type: ignore[arg-type]
        output_shape=contract.output_shape,
        coordinate_labels=labels,
        tensor_degree=contract.tensor_degree,
        o3_type=contract.o3_type,
        sign_class=contract.sign_class,
        required_components=contract.required_components,
        frame=frame,
        congruence=congruence,
        epoch_window=epoch_window,
        averaging_scale=averaging_scale,
        normalization=normalization,
        perturbative_order=perturbative_order,
        branch=branch,
        anchor_id=anchor_id,
        _construction_token=_SPEC_TOKEN,
    )


@dataclass(frozen=True)
class FunctionalDomainReport:
    status: FunctionalDomainStatus
    required_components: tuple[str, ...]
    missing_components: tuple[str, ...]
    mismatched_metadata: tuple[str, ...]
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.status) is not FunctionalDomainStatus:
            raise TensorFunctionalError(
                "domain status must be a FunctionalDomainStatus"
            )
        object.__setattr__(
            self,
            "required_components",
            _texts(self.required_components, "required_components"),
        )
        object.__setattr__(
            self,
            "missing_components",
            _texts(
                self.missing_components,
                "missing_components",
                empty_ok=True,
            ),
        )
        object.__setattr__(
            self,
            "mismatched_metadata",
            _texts(
                self.mismatched_metadata,
                "mismatched_metadata",
                empty_ok=True,
            ),
        )
        object.__setattr__(
            self,
            "reasons",
            _texts(self.reasons, "reasons", empty_ok=True),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "mismatched_metadata": list(self.mismatched_metadata),
            "missing_components": list(self.missing_components),
            "reasons": list(self.reasons),
            "required_components": list(self.required_components),
            "status": self.status.value,
        }


@dataclass(frozen=True)
class FunctionalCodomainReport:
    shape: tuple[int, ...]
    coordinate_labels: tuple[str, ...]
    o3_type: FunctionalO3Type
    tensor_degree: int

    def __post_init__(self) -> None:
        shape = tuple(
            _integer(value, "shape", minimum=1) for value in self.shape
        )
        labels = _texts(self.coordinate_labels, "coordinate_labels")
        if len(labels) != math.prod(shape):
            raise TensorFunctionalError(
                "codomain labels must cover flattened output shape"
            )
        if type(self.o3_type) is not FunctionalO3Type:
            raise TensorFunctionalError(
                "codomain o3_type must be a FunctionalO3Type"
            )
        object.__setattr__(self, "shape", shape)
        object.__setattr__(self, "coordinate_labels", labels)
        object.__setattr__(
            self,
            "tensor_degree",
            _integer(self.tensor_degree, "tensor_degree"),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "coordinate_labels": list(self.coordinate_labels),
            "o3_type": self.o3_type.value,
            "shape": list(self.shape),
            "tensor_degree": self.tensor_degree,
        }


@dataclass(frozen=True)
class FunctionalAnchorReport:
    status: FunctionalAnchorStatus
    requested_anchor_id: str | None
    resolved_anchor_id: str | None
    gauge: AnchorGaugeInterval | None
    margin: AnchorMarginReport | None
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.status) is not FunctionalAnchorStatus:
            raise TensorFunctionalError(
                "anchor status must be a FunctionalAnchorStatus"
            )
        if self.requested_anchor_id is not None:
            _text(self.requested_anchor_id, "requested_anchor_id")
        if self.resolved_anchor_id is not None:
            _text(self.resolved_anchor_id, "resolved_anchor_id")
        object.__setattr__(
            self,
            "reasons",
            _texts(self.reasons, "reasons", empty_ok=True),
        )
        numeric = self.status in {
            FunctionalAnchorStatus.DEFINED,
            FunctionalAnchorStatus.CONDITIONAL,
        }
        if numeric:
            if (
                type(self.gauge) is not AnchorGaugeInterval
                or type(self.margin) is not AnchorMarginReport
            ):
                raise TensorFunctionalError(
                    "numeric anchor reports require PR-254 gauge and margin"
                )
        elif self.gauge is not None or self.margin is not None:
            raise TensorFunctionalError(
                "non-numeric anchor reports must not carry gauge or margin"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "gauge": None if self.gauge is None else self.gauge.as_payload(),
            "margin": None if self.margin is None else self.margin.as_payload(),
            "reasons": list(self.reasons),
            "requested_anchor_id": self.requested_anchor_id,
            "resolved_anchor_id": self.resolved_anchor_id,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class FunctionalAdmissibilityReport:
    status: FunctionalAdmissibilityStatus
    sign_class: FunctionalSignClass
    signed_score_eligible: bool
    occupancy_eligible: bool
    exceedance_eligible: bool
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.status) is not FunctionalAdmissibilityStatus:
            raise TensorFunctionalError(
                "admissibility status must be a FunctionalAdmissibilityStatus"
            )
        if type(self.sign_class) is not FunctionalSignClass:
            raise TensorFunctionalError(
                "sign_class must be a FunctionalSignClass"
            )
        for name in (
            "signed_score_eligible",
            "occupancy_eligible",
            "exceedance_eligible",
        ):
            if type(getattr(self, name)) is not bool:
                raise TensorFunctionalError(f"{name} must be boolean")
        if (
            self.occupancy_eligible
            and self.sign_class is not FunctionalSignClass.SIGN_DEFINITE
        ):
            raise TensorFunctionalError(
                "occupancy requires a sign-definite functional"
            )
        object.__setattr__(
            self,
            "reasons",
            _texts(self.reasons, "reasons", empty_ok=True),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "exceedance_eligible": self.exceedance_eligible,
            "occupancy_eligible": self.occupancy_eligible,
            "reasons": list(self.reasons),
            "sign_class": self.sign_class.value,
            "signed_score_eligible": self.signed_score_eligible,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class FunctionalStressReport:
    status: FunctionalStressStatus
    point_estimate: float | None
    lower: float | None
    upper: float | None
    anchor_id: str | None
    interpretation: str = "PR254_TYPED_PREMISE_ANCHOR_STRESS"

    def __post_init__(self) -> None:
        if type(self.status) is not FunctionalStressStatus:
            raise TensorFunctionalError(
                "stress status must be a FunctionalStressStatus"
            )
        if self.interpretation != "PR254_TYPED_PREMISE_ANCHOR_STRESS":
            raise TensorFunctionalError("stress interpretation drifted")
        if self.status is FunctionalStressStatus.UNAVAILABLE:
            if any(
                value is not None
                for value in (self.point_estimate, self.lower, self.upper)
            ):
                raise TensorFunctionalError(
                    "unavailable stress must not carry numeric fields"
                )
            return
        lower = _real(self.lower, "lower")
        upper = _real(self.upper, "upper")
        if lower < 0.0 or upper < lower:
            raise TensorFunctionalError("stress interval must be non-negative")
        if self.status is FunctionalStressStatus.DEFINED:
            point = _real(self.point_estimate, "point_estimate")
            if point != lower or point != upper:
                raise TensorFunctionalError(
                    "defined stress point must equal both interval endpoints"
                )
            object.__setattr__(self, "point_estimate", point)
        elif self.point_estimate is not None:
            raise TensorFunctionalError(
                "conditional stress must not carry one point estimate"
            )
        _text(self.anchor_id, "anchor_id")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    def as_payload(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "interpretation": self.interpretation,
            "lower": self.lower,
            "point_estimate": self.point_estimate,
            "status": self.status.value,
            "upper": self.upper,
        }


@dataclass(frozen=True)
class TensorFunctionalResult:
    """Factory-derived result with value and authority fields kept separate."""

    spec: TensorFunctionalSpec
    source_state_id: str
    value: tuple[float, ...] | None
    domain: FunctionalDomainReport
    codomain: FunctionalCodomainReport
    anchor: FunctionalAnchorReport
    admissibility: FunctionalAdmissibilityReport
    stress: FunctionalStressReport
    transfer_source: str
    claim_ceiling: str = FUNCTIONAL_CLAIM_CEILING
    allowed_use: tuple[str, ...] = FUNCTIONAL_ALLOWED_USE
    forbidden_use: tuple[str, ...] = FUNCTIONAL_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise TensorFunctionalError(
                "TensorFunctionalResult must be created by "
                "evaluate_tensor_functional"
            )
        if type(self.spec) is not TensorFunctionalSpec:
            raise TensorFunctionalError("spec must be a TensorFunctionalSpec")
        _text(self.source_state_id, "source_state_id")
        _text(self.transfer_source, "transfer_source")
        if type(self.domain) is not FunctionalDomainReport:
            raise TensorFunctionalError(
                "domain must be a FunctionalDomainReport"
            )
        if type(self.codomain) is not FunctionalCodomainReport:
            raise TensorFunctionalError(
                "codomain must be a FunctionalCodomainReport"
            )
        if type(self.anchor) is not FunctionalAnchorReport:
            raise TensorFunctionalError(
                "anchor must be a FunctionalAnchorReport"
            )
        if type(self.admissibility) is not FunctionalAdmissibilityReport:
            raise TensorFunctionalError(
                "admissibility must be a FunctionalAdmissibilityReport"
            )
        if type(self.stress) is not FunctionalStressReport:
            raise TensorFunctionalError(
                "stress must be a FunctionalStressReport"
            )
        if self.codomain.shape != self.spec.output_shape:
            raise TensorFunctionalError("codomain shape drifted from spec")
        if self.domain.status is FunctionalDomainStatus.ADMISSIBLE:
            if self.value is None:
                raise TensorFunctionalError(
                    "admissible domain requires a functional value"
                )
            values = tuple(
                _real(value, f"value[{index}]")
                for index, value in enumerate(self.value)
            )
            if len(values) != math.prod(self.codomain.shape):
                raise TensorFunctionalError(
                    "value length must match flattened codomain shape"
                )
            object.__setattr__(self, "value", values)
        elif self.value is not None:
            raise TensorFunctionalError(
                "inadmissible domain must not carry a value"
            )
        if self.claim_ceiling != FUNCTIONAL_CLAIM_CEILING:
            raise TensorFunctionalError("result claim ceiling drifted")
        if tuple(self.allowed_use) != FUNCTIONAL_ALLOWED_USE:
            raise TensorFunctionalError("result allowed-use lane drifted")
        if tuple(self.forbidden_use) != FUNCTIONAL_FORBIDDEN_USE:
            raise TensorFunctionalError("result forbidden-use lane drifted")

    @property
    def result_id(self) -> str:
        return _sha256_payload(self.as_payload())

    @property
    def scalar_value(self) -> float:
        if self.value is None or self.codomain.shape != (1,):
            raise TensorFunctionalError("result is not an available scalar")
        return self.value[0]

    def as_payload(self) -> dict[str, object]:
        return {
            "admissibility": self.admissibility.as_payload(),
            "allowed_use": list(self.allowed_use),
            "anchor": self.anchor.as_payload(),
            "claim_ceiling": self.claim_ceiling,
            "codomain": self.codomain.as_payload(),
            "domain": self.domain.as_payload(),
            "forbidden_use": list(self.forbidden_use),
            "functional_spec": self.spec.to_payload(),
            "functional_spec_id": self.spec.spec_id,
            "schema": "HTT_TENSOR_FUNCTIONAL_RESULT_V1",
            "source_state_id": self.source_state_id,
            "stress": self.stress.as_payload(),
            "transfer_source": self.transfer_source,
            "value": None if self.value is None else list(self.value),
        }


def _clone_body(body: AnchorBodySpec) -> AnchorBodySpec:
    """Re-run the PR-254 constructor so post-construction mutation fails."""

    blocks = tuple(
        AnchorBlockSpec(
            block_id=block.block_id,
            coordinate_indices=tuple(block.coordinate_indices),
            radius=block.radius,
            availability=block.availability,
            unavailable_reason=block.unavailable_reason,
        )
        for block in body.blocks
    )
    halfspaces = tuple(
        PolytopeHalfspace(
            normal=tuple(halfspace.normal),
            bound=halfspace.bound,
        )
        for halfspace in body.halfspaces
    )
    return AnchorBodySpec(
        body_id=body.body_id,
        geometry=body.geometry,
        coordinate_labels=tuple(body.coordinate_labels),
        frame=body.frame,
        normalization=body.normalization,
        perturbative_order=body.perturbative_order,
        branch=body.branch,
        premise_identity=body.premise_identity,
        blocks=blocks,
        quadratic_form=tuple(tuple(row) for row in body.quadratic_form),
        halfspaces=halfspaces,
        availability=body.availability,
        unavailable_reason=body.unavailable_reason,
        assumptions=tuple(body.assumptions),
        allowed_use=tuple(body.allowed_use),
        forbidden_use=tuple(body.forbidden_use),
    )


def _clone_anchor(
    anchor: AnchorBodySpec | AnchorFamily,
) -> AnchorBodySpec | AnchorFamily:
    if type(anchor) is AnchorBodySpec:
        return _clone_body(anchor)
    if type(anchor) is not AnchorFamily:
        raise TensorFunctionalError(
            "anchor must be an exact PR-254 AnchorBodySpec or AnchorFamily"
        )
    return AnchorFamily(
        family_id=anchor.family_id,
        kind=anchor.kind,
        bodies=tuple(_clone_body(body) for body in anchor.bodies),
        nuisance_identity=anchor.nuisance_identity,
        optimizer_contract=anchor.optimizer_contract,
        assumptions=tuple(anchor.assumptions),
        coordinate_labels=tuple(anchor.coordinate_labels),
        frame=anchor.frame,
        normalization=anchor.normalization,
        perturbative_order=anchor.perturbative_order,
        branch=anchor.branch,
    )


def _anchor_identity(anchor: AnchorBodySpec | AnchorFamily) -> str:
    return anchor.body_id if type(anchor) is AnchorBodySpec else anchor.family_id


def _component(
    state: JointAnisotropyState,
    name: str,
) -> tuple[float, ...] | float | MissingComponent:
    if name == "sigma_stf5":
        return state.congruence_kinematics.sigma_stf5
    if name == "omega_axial3":
        return state.congruence_kinematics.omega_axial3
    if name == "acceleration_polar3":
        return state.congruence_kinematics.acceleration_polar3
    if name == "beta_RM":
        return state.velocity_frames.beta_RM
    if name == "beta_MO":
        return state.velocity_frames.beta_MO
    if name == "beta_RO":
        return state.velocity_frames.beta_RO
    if name == "delta_omega_k":
        return state.geometry_state.delta_omega_k
    raise TensorFunctionalError(f"unknown registered component {name!r}")


def _evaluate_operator(
    state: JointAnisotropyState,
    operator: TensorFunctionalOperator,
) -> tuple[float, ...]:
    sigma = stf5_to_matrix(state.congruence_kinematics.sigma_stf5)
    omega = np.asarray(state.congruence_kinematics.omega_axial3, dtype=float)
    beta_rm_value = state.velocity_frames.beta_RM
    beta_rm = (
        None
        if type(beta_rm_value) is MissingComponent
        else np.asarray(beta_rm_value, dtype=float)
    )
    if operator is TensorFunctionalOperator.SIGMA_STF5:
        return tuple(state.congruence_kinematics.sigma_stf5)
    if operator is TensorFunctionalOperator.OMEGA_AXIAL3:
        return tuple(state.congruence_kinematics.omega_axial3)
    if operator is TensorFunctionalOperator.ACCELERATION_POLAR3:
        value = state.congruence_kinematics.acceleration_polar3
        assert type(value) is not MissingComponent
        return tuple(value)
    if operator is TensorFunctionalOperator.BETA_RM_POLAR3:
        assert beta_rm is not None
        return tuple(float(value) for value in beta_rm)
    if operator is TensorFunctionalOperator.BETA_MO_POLAR3:
        value = state.velocity_frames.beta_MO
        assert type(value) is not MissingComponent
        return tuple(value)
    if operator is TensorFunctionalOperator.BETA_RO_POLAR3:
        value = state.velocity_frames.beta_RO
        assert type(value) is not MissingComponent
        return tuple(value)
    if operator is TensorFunctionalOperator.DELTA_OMEGA_K:
        return (state.geometry_state.delta_omega_k,)
    if operator is TensorFunctionalOperator.TR_SIGMA2:
        return (float(np.trace(sigma @ sigma)),)
    if operator is TensorFunctionalOperator.TR_SIGMA3:
        return (float(np.trace(sigma @ sigma @ sigma)),)
    if operator is TensorFunctionalOperator.OMEGA2:
        return (float(omega @ omega),)
    if operator is TensorFunctionalOperator.BETA_RM2:
        assert beta_rm is not None
        return (float(beta_rm @ beta_rm),)
    if operator is TensorFunctionalOperator.BETA_RM_DOT_OMEGA:
        assert beta_rm is not None
        return (float(beta_rm @ omega),)
    if operator is TensorFunctionalOperator.BETA_RM_SIGMA_BETA_RM:
        assert beta_rm is not None
        return (float(beta_rm @ sigma @ beta_rm),)
    raise TensorFunctionalError(f"unhandled operator {operator.value}")


def _empty_anchor_report(
    status: FunctionalAnchorStatus,
    *,
    requested: str | None,
    resolved: str | None = None,
    reasons: tuple[str, ...] = (),
) -> FunctionalAnchorReport:
    return FunctionalAnchorReport(
        status=status,
        requested_anchor_id=requested,
        resolved_anchor_id=resolved,
        gauge=None,
        margin=None,
        reasons=reasons,
    )


def _anchor_report(
    spec: TensorFunctionalSpec,
    value: tuple[float, ...] | None,
    anchor: AnchorBodySpec | AnchorFamily | None,
) -> FunctionalAnchorReport:
    if spec.anchor_id is None:
        if anchor is not None:
            return _empty_anchor_report(
                FunctionalAnchorStatus.CHANNEL_MISMATCH,
                requested=None,
                resolved=_anchor_identity(anchor),
                reasons=("functional did not register an anchor_id",),
            )
        return _empty_anchor_report(
            FunctionalAnchorStatus.NOT_REQUESTED,
            requested=None,
        )
    if anchor is None or value is None:
        return _empty_anchor_report(
            FunctionalAnchorStatus.ANCHOR_UNAVAILABLE,
            requested=spec.anchor_id,
            reasons=(
                "anchor input or functional value is unavailable",
            ),
        )
    try:
        checked = _clone_anchor(anchor)
    except AnchorGeometryError as exc:
        message = str(exc)
        rank_tokens = (
            "positive definite",
            "span the coordinate space",
            "cover every coordinate exactly once",
        )
        if any(token in message for token in rank_tokens):
            status = FunctionalAnchorStatus.RANK_DEFICIENT
        elif "centrally symmetric" in message:
            status = FunctionalAnchorStatus.NON_COMPACT_SUPPORT
        else:
            status = FunctionalAnchorStatus.ANCHOR_UNAVAILABLE
        return _empty_anchor_report(
            status,
            requested=spec.anchor_id,
            resolved=_anchor_identity(anchor),
            reasons=(message,),
        )
    resolved = _anchor_identity(checked)
    if resolved != spec.anchor_id:
        return _empty_anchor_report(
            FunctionalAnchorStatus.CHANNEL_MISMATCH,
            requested=spec.anchor_id,
            resolved=resolved,
            reasons=("anchor identity does not match functional anchor_id",),
        )
    vector = AnchorVector(
        vector_id=_sha256_payload(
            {
                "functional_spec_id": spec.spec_id,
                "value_hex": [float(item).hex() for item in value],
            }
        ),
        coordinate_labels=spec.coordinate_labels,
        values=value,
        frame=spec.frame,
        normalization=spec.normalization,
        perturbative_order=spec.perturbative_order,
        branch=spec.branch,
    )
    gauge = evaluate_anchor_gauge(checked, vector)
    mapped = {
        AnchorGaugeStatus.DEFINED: FunctionalAnchorStatus.DEFINED,
        AnchorGaugeStatus.FINITE_CONDITIONAL: (
            FunctionalAnchorStatus.CONDITIONAL
        ),
        AnchorGaugeStatus.NONCONVEX_CONDITIONAL_ONLY: (
            FunctionalAnchorStatus.CONDITIONAL
        ),
        AnchorGaugeStatus.OPTIMIZER_REQUIRED: (
            FunctionalAnchorStatus.OPTIMIZER_REQUIRED
        ),
        AnchorGaugeStatus.ANCHOR_UNAVAILABLE: (
            FunctionalAnchorStatus.ANCHOR_UNAVAILABLE
        ),
        AnchorGaugeStatus.CHANNEL_MISMATCH: (
            FunctionalAnchorStatus.CHANNEL_MISMATCH
        ),
    }[gauge.status]
    if mapped not in {
        FunctionalAnchorStatus.DEFINED,
        FunctionalAnchorStatus.CONDITIONAL,
    }:
        return _empty_anchor_report(
            mapped,
            requested=spec.anchor_id,
            resolved=resolved,
            reasons=(f"PR-254 gauge status {gauge.status.value}",),
        )
    margin = build_anchor_margin_report(gauge)
    return FunctionalAnchorReport(
        status=mapped,
        requested_anchor_id=spec.anchor_id,
        resolved_anchor_id=resolved,
        gauge=gauge,
        margin=margin,
        reasons=(),
    )


def _stress_report(anchor: FunctionalAnchorReport) -> FunctionalStressReport:
    if anchor.gauge is None:
        return FunctionalStressReport(
            status=FunctionalStressStatus.UNAVAILABLE,
            point_estimate=None,
            lower=None,
            upper=None,
            anchor_id=anchor.resolved_anchor_id or anchor.requested_anchor_id,
        )
    gauge = anchor.gauge
    assert gauge.lower is not None and gauge.upper is not None
    if anchor.status is FunctionalAnchorStatus.DEFINED:
        return FunctionalStressReport(
            status=FunctionalStressStatus.DEFINED,
            point_estimate=gauge.lower,
            lower=gauge.lower,
            upper=gauge.upper,
            anchor_id=anchor.resolved_anchor_id,
        )
    return FunctionalStressReport(
        status=FunctionalStressStatus.CONDITIONAL,
        point_estimate=None,
        lower=gauge.lower,
        upper=gauge.upper,
        anchor_id=anchor.resolved_anchor_id,
    )


def evaluate_tensor_functional(
    state: JointAnisotropyState,
    spec: TensorFunctionalSpec,
    *,
    anchor: AnchorBodySpec | AnchorFamily | None = None,
) -> TensorFunctionalResult:
    """Evaluate one registered functional with fail-closed typed reports."""

    if type(state) is not JointAnisotropyState:
        raise TypeError("state must be an exact JointAnisotropyState")
    if type(spec) is not TensorFunctionalSpec:
        raise TypeError("spec must be an exact TensorFunctionalSpec")
    try:
        replay = JointAnisotropyState.from_payload(state.to_payload())
    except JointAnisotropyStateError as exc:
        raise TensorFunctionalError(
            "joint state failed canonical replay"
        ) from exc
    if replay.content_id != state.content_id:
        raise TensorFunctionalError("joint state content identity drifted")

    comparisons = {
        "frame": (spec.frame, state.frame),
        "congruence": (spec.congruence, state.congruence),
        "epoch_window": (spec.epoch_window, state.epoch_window),
        "averaging_scale": (
            spec.averaging_scale,
            state.averaging_scale,
        ),
        "perturbative_order": (
            spec.perturbative_order,
            state.perturbative_order,
        ),
    }
    mismatches = tuple(
        name for name, (declared, actual) in comparisons.items()
        if declared != actual
    )
    missing = tuple(
        name
        for name in spec.required_components
        if type(_component(state, name)) is MissingComponent
    )
    if mismatches:
        domain = FunctionalDomainReport(
            status=FunctionalDomainStatus.METADATA_MISMATCH,
            required_components=spec.required_components,
            missing_components=(),
            mismatched_metadata=mismatches,
            reasons=("functional and joint-state metadata do not match",),
        )
        value = None
    elif missing:
        domain = FunctionalDomainReport(
            status=FunctionalDomainStatus.MISSING_COMPONENT,
            required_components=spec.required_components,
            missing_components=missing,
            mismatched_metadata=(),
            reasons=tuple(
                (
                    _component(state, name).reason
                    if type(_component(state, name)) is MissingComponent
                    else ""
                )
                for name in missing
            ),
        )
        value = None
    else:
        domain = FunctionalDomainReport(
            status=FunctionalDomainStatus.ADMISSIBLE,
            required_components=spec.required_components,
            missing_components=(),
            mismatched_metadata=(),
            reasons=(),
        )
        value = _evaluate_operator(state, spec.operator)

    codomain = FunctionalCodomainReport(
        shape=spec.output_shape,
        coordinate_labels=spec.coordinate_labels,
        o3_type=spec.o3_type,
        tensor_degree=spec.tensor_degree,
    )
    anchor_report = _anchor_report(spec, value, anchor)
    anchor_usable = anchor_report.status in {
        FunctionalAnchorStatus.DEFINED,
        FunctionalAnchorStatus.CONDITIONAL,
    }
    domain_usable = domain.status is FunctionalDomainStatus.ADMISSIBLE
    occupancy_eligible = (
        domain_usable
        and anchor_usable
        and spec.sign_class is FunctionalSignClass.SIGN_DEFINITE
    )
    admissibility = FunctionalAdmissibilityReport(
        status=(
            FunctionalAdmissibilityStatus.ADMISSIBLE
            if domain_usable
            else FunctionalAdmissibilityStatus.ABSTAIN
        ),
        sign_class=spec.sign_class,
        signed_score_eligible=domain_usable and anchor_usable,
        occupancy_eligible=occupancy_eligible,
        exceedance_eligible=domain_usable,
        reasons=(
            ()
            if domain_usable
            else ("functional domain is not admissible",)
        )
        + (
            ()
            if spec.sign_class is FunctionalSignClass.SIGN_DEFINITE
            else ("signed/equivariant functional cannot carry occupancy",)
        ),
    )
    return TensorFunctionalResult(
        spec=spec,
        source_state_id=state.content_id,
        value=value,
        domain=domain,
        codomain=codomain,
        anchor=anchor_report,
        admissibility=admissibility,
        stress=_stress_report(anchor_report),
        transfer_source=state.transfer_source.value,
        _construction_token=_RESULT_TOKEN,
    )


def revalidate_tensor_functional_result(
    result: TensorFunctionalResult,
    state: JointAnisotropyState,
    *,
    anchor: AnchorBodySpec | AnchorFamily | None = None,
) -> TensorFunctionalResult:
    """Replay a result from its bound state/spec and reject stale mutation."""

    if type(result) is not TensorFunctionalResult:
        raise TensorFunctionalError(
            "result must be an exact TensorFunctionalResult"
        )
    rebuilt = evaluate_tensor_functional(
        state,
        result.spec,
        anchor=anchor,
    )
    if rebuilt.as_payload() != result.as_payload():
        raise TensorFunctionalError(
            "functional result fields do not match bound state/spec/anchor"
        )
    return rebuilt


__all__ = [
    "FUNCTIONAL_ALLOWED_USE",
    "FUNCTIONAL_CLAIM_CEILING",
    "FUNCTIONAL_FORBIDDEN_USE",
    "FunctionalAdmissibilityReport",
    "FunctionalAdmissibilityStatus",
    "FunctionalAnchorReport",
    "FunctionalAnchorStatus",
    "FunctionalCodomainReport",
    "FunctionalDomainReport",
    "FunctionalDomainStatus",
    "FunctionalO3Type",
    "FunctionalSignClass",
    "FunctionalStressReport",
    "FunctionalStressStatus",
    "TensorFunctionalError",
    "TensorFunctionalOperator",
    "TensorFunctionalResult",
    "TensorFunctionalSpec",
    "build_tensor_functional_spec",
    "evaluate_tensor_functional",
    "revalidate_tensor_functional_result",
]

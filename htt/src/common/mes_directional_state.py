"""Typed observer-space MES directional states and refusal boundaries.

The types here keep a direction-indexed observable, its O(3) moments, a
positive active MES anchor, and any future physical response separate.  They
provide diagnostic observer-space coordinates only.  A scalar anchor cannot
create a vector or STF tensor, and no physical stress is defined without a
channel-matched response and numerator.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Real
import re
from typing import Sequence

import numpy as np

from common.statistical_foundations import (
    AnchorConditioning,
    AnchorStatus,
    MESAnchorSpec,
)


class DirectionalBridgeError(ValueError):
    """Raised when a directional or claim boundary is incomplete."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DirectionalFieldParity(_StringEnum):
    """Intrinsic parity of the direction-indexed scalar field."""

    SCALAR_EVEN = "SCALAR_EVEN"
    PSEUDOSCALAR_ODD = "PSEUDOSCALAR_ODD"


class DirectionConvention(_StringEnum):
    """Registered component/transformation convention for this bridge."""

    RIGHT_HANDED_ACTIVE_O3 = "RIGHT_HANDED_ACTIVE_O3"


class VectorO3Representation(_StringEnum):
    POLAR = "POLAR_VECTOR"
    AXIAL = "AXIAL_VECTOR"


class TensorO3Representation(_StringEnum):
    EVEN_STF2 = "EVEN_STF2"
    ODD_STF2 = "ODD_STF2"


class DirectionalEstimatorKind(_StringEnum):
    FULL_SKY_QUADRATURE = "FULL_SKY_QUADRATURE"
    WEIGHTED_JOINT_HARMONIC_FIT = "WEIGHTED_JOINT_HARMONIC_FIT"


class PhysicalStressReadiness(_StringEnum):
    BLOCKED_PHYSICAL_RESPONSE_REQUIRED = "BLOCKED_PHYSICAL_RESPONSE_REQUIRED"
    BLOCKED_CHANNEL_MATCH = "BLOCKED_CHANNEL_MATCH"
    RESPONSE_BOUND_NUMERATOR_REQUIRED = "RESPONSE_BOUND_NUMERATOR_REQUIRED"


_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ZERO_SHAPE_TOL = 1.0e-15
_REALIZABILITY_TOL = 1.0e-10
_BANDLIMIT_COMPONENT_TOL = 1.0e-10
MAX_DIRECTIONAL_DESIGN_CONDITION = 1.0e8
_IDENTITY_ROLE = "REPRODUCIBILITY_IDENTITY_NOT_AUTHORITY"
_DIRECTIONAL_ROLE = "DIRECTION_INDEXED_SCALAR_MOMENT_ESTIMATE"
_OBSERVER_ROLE = "OBSERVER_SPACE_MES_INDEX_NOT_PHYSICAL_STRESS"
_DIRECTIONAL_SEMANTICS_STATUS = "DECLARED_UNVERIFIED_BANDLIMIT_AND_PARITY"
_SCALAR_REFUSAL = (
    "BLOCKED_SCALAR_TO_TENSOR_FABRICATION: BLOCKED_DIRECTIONAL_SUPPORT"
)


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DirectionalBridgeError(f"{name} must be non-empty trimmed text")
    return value


def _content_identity(value: object, name: str) -> str:
    text = _required_text(value, name)
    if _SHA256_RE.fullmatch(text) is None:
        raise DirectionalBridgeError(f"{name} must be a sha256 content identity")
    return text


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise DirectionalBridgeError(f"{name} must be a finite real number")
    result = float(value)
    if not math.isfinite(result):
        raise DirectionalBridgeError(f"{name} must be a finite real number")
    return result


def _vector3(value: object, name: str) -> tuple[float, float, float]:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DirectionalBridgeError(f"{name} must be a finite 3-vector") from exc
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        raise DirectionalBridgeError(f"{name} must be a finite 3-vector")
    return tuple(float(item) for item in array)


def _stf2(value: object, name: str) -> tuple[tuple[float, float, float], ...]:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DirectionalBridgeError(
            f"{name} must be a finite symmetric trace-free 3x3 tensor"
        ) from exc
    scale = max(1.0, float(np.linalg.norm(array))) if array.shape == (3, 3) else 1.0
    if (
        array.shape != (3, 3)
        or not np.all(np.isfinite(array))
        or not np.allclose(array, array.T, rtol=0.0, atol=1e-12 * scale)
        or not math.isclose(float(np.trace(array)), 0.0, rel_tol=0.0, abs_tol=1e-12 * scale)
    ):
        raise DirectionalBridgeError(
            f"{name} must be a finite symmetric trace-free 3x3 tensor"
        )
    symmetric = 0.5 * (array + array.T)
    symmetric -= np.eye(3) * float(np.trace(symmetric)) / 3.0
    return tuple(tuple(float(item) for item in row) for row in symmetric)


def _canonical_identity(payload: object, *, role: str) -> str:
    encoded = json.dumps(
        {"role": role, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _representations(
    parity: DirectionalFieldParity,
) -> tuple[VectorO3Representation, TensorO3Representation]:
    if parity is DirectionalFieldParity.SCALAR_EVEN:
        return VectorO3Representation.POLAR, TensorO3Representation.EVEN_STF2
    if parity is DirectionalFieldParity.PSEUDOSCALAR_ODD:
        return VectorO3Representation.AXIAL, TensorO3Representation.ODD_STF2
    raise DirectionalBridgeError("field_parity must be a DirectionalFieldParity")


def _validate_declared_bandlimit(
    *,
    monopole: float,
    dipole: Sequence[float],
    stf2: Sequence[Sequence[float]],
    field_bandlimit: int,
) -> None:
    """Reject component-level contradictions without claiming leakage proof."""

    vector_norm = float(np.linalg.norm(np.asarray(dipole, dtype=float)))
    tensor_norm = float(np.linalg.norm(np.asarray(stf2, dtype=float)))
    scale = max(1.0, abs(monopole), vector_norm, tensor_norm)
    tolerance = _BANDLIMIT_COMPONENT_TOL * scale
    if field_bandlimit == 0 and (vector_norm > tolerance or tensor_norm > tolerance):
        raise DirectionalBridgeError(
            "BLOCKED_DIRECTIONAL_LEAKAGE: declared ell=0 contradicts recovered moments"
        )
    if field_bandlimit == 1 and tensor_norm > tolerance:
        raise DirectionalBridgeError(
            "BLOCKED_DIRECTIONAL_LEAKAGE: declared ell<=1 contradicts recovered STF2"
        )


def _directional_estimator_identity(
    *,
    kind: DirectionalEstimatorKind,
    support_identity: str,
    weight_identity: str,
    mask_identity: str,
    field_identity: str,
    transfer_identity: str,
    covariance_identity: str,
    direction_frame: str,
    direction_convention: DirectionConvention,
    parity: DirectionalFieldParity,
    field_quantity: str,
    field_units: str,
    field_bandlimit: int,
    support_size: int,
    design_rank: int,
    design_condition: float,
    max_design_condition: float,
    residual: float,
) -> str:
    normalization = (
        "V=3/(4pi) integral(q n); T=15/(8pi) integral(q STF(nn))"
        if kind is DirectionalEstimatorKind.FULL_SKY_QUADRATURE
        else "weighted joint fit: monopole + polar/axial dipole + five STF2 coordinates"
    )
    return _canonical_identity(
        {
            "kind": kind.value,
            "support_identity": support_identity,
            "weight_identity": weight_identity,
            "mask_identity": mask_identity,
            "field_identity": field_identity,
            "transfer_identity": transfer_identity,
            "covariance_identity": covariance_identity,
            "direction_frame": direction_frame,
            "direction_convention": direction_convention.value,
            "parity": parity.value,
            "directional_semantics_status": _DIRECTIONAL_SEMANTICS_STATUS,
            "field_quantity": field_quantity,
            "field_units": field_units,
            "field_bandlimit": field_bandlimit,
            "support_size": support_size,
            "design_rank": design_rank,
            "design_condition_float_hex": design_condition.hex(),
            "max_design_condition_float_hex": max_design_condition.hex(),
            "weighted_residual_float_hex": residual.hex(),
            "normalization": normalization,
        },
        role="mes_directional_estimator",
    )


@dataclass(frozen=True)
class DirectionalMomentEstimate:
    """Bound vector/STF moments of one genuinely direction-indexed field."""

    monopole: float
    dipole: tuple[float, float, float]
    stf2: tuple[tuple[float, float, float], ...]
    field_parity: DirectionalFieldParity
    vector_representation: VectorO3Representation
    tensor_representation: TensorO3Representation
    estimator_kind: DirectionalEstimatorKind
    direction_frame: str
    direction_convention: DirectionConvention
    field_quantity: str
    field_units: str
    field_bandlimit: int
    support_identity: str
    weight_identity: str
    mask_identity: str
    transfer_identity: str
    field_identity: str
    covariance_identity: str
    estimator_identity: str
    support_size: int
    design_rank: int
    design_condition_number: float
    max_design_condition_number: float
    weighted_residual_norm: float
    identity_role: str = _IDENTITY_ROLE
    methodology_role: str = _DIRECTIONAL_ROLE
    realizability_status: str = "SIGNED_FIELD_NOT_A_PROBABILITY_MEASURE"
    directional_semantics_status: str = _DIRECTIONAL_SEMANTICS_STATUS

    def __post_init__(self) -> None:
        object.__setattr__(self, "monopole", _finite_real(self.monopole, "monopole"))
        object.__setattr__(self, "dipole", _vector3(self.dipole, "dipole"))
        object.__setattr__(self, "stf2", _stf2(self.stf2, "stf2"))
        if not isinstance(self.field_parity, DirectionalFieldParity):
            raise DirectionalBridgeError(
                "field_parity must be a DirectionalFieldParity"
            )
        expected_vector, expected_tensor = _representations(self.field_parity)
        if (
            self.vector_representation is not expected_vector
            or self.tensor_representation is not expected_tensor
        ):
            raise DirectionalBridgeError("O3 representation does not match field parity")
        if not isinstance(self.estimator_kind, DirectionalEstimatorKind):
            raise DirectionalBridgeError(
                "estimator_kind must be a DirectionalEstimatorKind"
            )
        for name in ("direction_frame", "field_quantity"):
            _required_text(getattr(self, name), name)
        if self.direction_convention is not DirectionConvention.RIGHT_HANDED_ACTIVE_O3:
            raise DirectionalBridgeError(
                "direction_convention must be RIGHT_HANDED_ACTIVE_O3"
            )
        if self.field_units != "dimensionless":
            raise DirectionalBridgeError(
                "field_units must be dimensionless for an MES anchor coordinate"
            )
        if (
            isinstance(self.field_bandlimit, bool)
            or not isinstance(self.field_bandlimit, int)
            or not 0 <= self.field_bandlimit <= 2
        ):
            raise DirectionalBridgeError(
                "BLOCKED_DIRECTIONAL_LEAKAGE: field_bandlimit must be in [0, 2]"
            )
        _validate_declared_bandlimit(
            monopole=self.monopole,
            dipole=self.dipole,
            stf2=self.stf2,
            field_bandlimit=self.field_bandlimit,
        )
        for name in (
            "support_identity",
            "weight_identity",
            "mask_identity",
            "transfer_identity",
            "field_identity",
            "covariance_identity",
            "estimator_identity",
        ):
            _content_identity(getattr(self, name), name)
        if isinstance(self.support_size, bool) or not isinstance(self.support_size, int):
            raise DirectionalBridgeError("support_size must be a positive integer")
        if self.support_size <= 0:
            raise DirectionalBridgeError("support_size must be a positive integer")
        if isinstance(self.design_rank, bool) or not isinstance(self.design_rank, int):
            raise DirectionalBridgeError("design_rank must be an integer in [1, 9]")
        if not 1 <= self.design_rank <= 9:
            raise DirectionalBridgeError("design_rank must be an integer in [1, 9]")
        design_condition = _finite_real(
            self.design_condition_number, "design_condition_number"
        )
        maximum_condition = _finite_real(
            self.max_design_condition_number, "max_design_condition_number"
        )
        if (
            design_condition < 1.0
            or maximum_condition != MAX_DIRECTIONAL_DESIGN_CONDITION
            or design_condition > maximum_condition
        ):
            raise DirectionalBridgeError(
                "BLOCKED_DIRECTIONAL_SUPPORT: directional design is ill-conditioned"
            )
        object.__setattr__(self, "design_condition_number", design_condition)
        object.__setattr__(self, "max_design_condition_number", maximum_condition)
        residual = _finite_real(
            self.weighted_residual_norm, "weighted_residual_norm"
        )
        if residual < 0.0:
            raise DirectionalBridgeError("weighted_residual_norm must be non-negative")
        object.__setattr__(self, "weighted_residual_norm", residual)
        if self.identity_role != _IDENTITY_ROLE or self.methodology_role != _DIRECTIONAL_ROLE:
            raise DirectionalBridgeError("directional estimate semantics drifted")
        if self.realizability_status != "SIGNED_FIELD_NOT_A_PROBABILITY_MEASURE":
            raise DirectionalBridgeError(
                "directional field cannot claim a probability-measure certificate"
            )
        if self.directional_semantics_status != _DIRECTIONAL_SEMANTICS_STATUS:
            raise DirectionalBridgeError(
                "directional bandlimit/parity semantics cannot be self-promoted"
            )
        expected_identity = _directional_estimator_identity(
            kind=self.estimator_kind,
            support_identity=self.support_identity,
            weight_identity=self.weight_identity,
            mask_identity=self.mask_identity,
            field_identity=self.field_identity,
            transfer_identity=self.transfer_identity,
            covariance_identity=self.covariance_identity,
            direction_frame=self.direction_frame,
            direction_convention=self.direction_convention,
            parity=self.field_parity,
            field_quantity=self.field_quantity,
            field_units=self.field_units,
            field_bandlimit=self.field_bandlimit,
            support_size=self.support_size,
            design_rank=self.design_rank,
            design_condition=design_condition,
            max_design_condition=maximum_condition,
            residual=residual,
        )
        if self.estimator_identity != expected_identity:
            raise DirectionalBridgeError(
                "estimator_identity does not bind estimator content"
            )


def make_directional_moment_estimate(
    *,
    monopole: float,
    dipole: Sequence[float],
    stf2: Sequence[Sequence[float]],
    field_parity: DirectionalFieldParity,
    estimator_kind: DirectionalEstimatorKind,
    direction_frame: str,
    direction_convention: DirectionConvention,
    field_quantity: str,
    field_units: str,
    field_bandlimit: int,
    support_identity: str,
    weight_identity: str,
    mask_identity: str,
    transfer_identity: str,
    field_identity: str,
    covariance_identity: str,
    support_size: int,
    design_rank: int,
    design_condition_number: float,
    max_design_condition_number: float,
    weighted_residual_norm: float,
) -> DirectionalMomentEstimate:
    """Build a validated estimate; this function accepts no scalar-only path."""

    if direction_convention is not DirectionConvention.RIGHT_HANDED_ACTIVE_O3:
        raise DirectionalBridgeError(
            "direction_convention must be RIGHT_HANDED_ACTIVE_O3"
        )
    vector_representation, tensor_representation = _representations(field_parity)
    estimator_identity = _directional_estimator_identity(
        kind=estimator_kind,
        support_identity=support_identity,
        weight_identity=weight_identity,
        mask_identity=mask_identity,
        field_identity=field_identity,
        transfer_identity=transfer_identity,
        covariance_identity=covariance_identity,
        direction_frame=direction_frame,
        direction_convention=direction_convention,
        parity=field_parity,
        field_quantity=field_quantity,
        field_units=field_units,
        field_bandlimit=field_bandlimit,
        support_size=support_size,
        design_rank=design_rank,
        design_condition=float(design_condition_number),
        max_design_condition=float(max_design_condition_number),
        residual=float(weighted_residual_norm),
    )
    return DirectionalMomentEstimate(
        monopole=monopole,
        dipole=_vector3(dipole, "dipole"),
        stf2=_stf2(stf2, "stf2"),
        field_parity=field_parity,
        vector_representation=vector_representation,
        tensor_representation=tensor_representation,
        estimator_kind=estimator_kind,
        direction_frame=direction_frame,
        direction_convention=direction_convention,
        field_quantity=field_quantity,
        field_units=field_units,
        field_bandlimit=field_bandlimit,
        support_identity=support_identity,
        weight_identity=weight_identity,
        mask_identity=mask_identity,
        transfer_identity=transfer_identity,
        field_identity=field_identity,
        covariance_identity=covariance_identity,
        estimator_identity=estimator_identity,
        support_size=support_size,
        design_rank=design_rank,
        design_condition_number=design_condition_number,
        max_design_condition_number=max_design_condition_number,
        weighted_residual_norm=weighted_residual_norm,
    )


@dataclass(frozen=True)
class SphericalSecondMomentCertificate:
    """Scoped zero-mean PSD trace-one second-moment cone certificate."""

    mean: tuple[float, float, float]
    second_moment: tuple[tuple[float, float, float], ...]
    eigenvalues: tuple[float, float, float]
    support_identity: str
    status: str = "PSD_TRACE_ONE_ZERO_MEAN_VERIFIED"
    construction_scope: str = "ANTIPODAL_SECOND_MOMENT_CONE_ONLY"
    higher_moment_claim: bool = False
    dynamical_attainability_claim: bool = False

    def __post_init__(self) -> None:
        if self.status != "PSD_TRACE_ONE_ZERO_MEAN_VERIFIED":
            raise DirectionalBridgeError("realizability certificate status drifted")
        if self.construction_scope != "ANTIPODAL_SECOND_MOMENT_CONE_ONLY":
            raise DirectionalBridgeError("realizability scope drifted")
        if self.higher_moment_claim or self.dynamical_attainability_claim:
            raise DirectionalBridgeError("second-moment certificate claim inflated")
        support_identity = _content_identity(
            self.support_identity, "support_identity"
        )
        mean = np.asarray(_vector3(self.mean, "mean"), dtype=float)
        try:
            second = np.asarray(self.second_moment, dtype=float)
            supplied_eigenvalues = np.asarray(self.eigenvalues, dtype=float)
        except (TypeError, ValueError) as exc:
            raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY") from exc
        if (
            second.shape != (3, 3)
            or supplied_eigenvalues.shape != (3,)
            or not np.all(np.isfinite(second))
            or not np.all(np.isfinite(supplied_eigenvalues))
            or not np.allclose(
                second, second.T, rtol=0.0, atol=_REALIZABILITY_TOL
            )
            or np.linalg.norm(mean) > _REALIZABILITY_TOL
            or not math.isclose(
                float(np.trace(second)),
                1.0,
                rel_tol=0.0,
                abs_tol=_REALIZABILITY_TOL,
            )
        ):
            raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY")
        symmetric = 0.5 * (second + second.T)
        expected_eigenvalues = np.linalg.eigvalsh(symmetric)
        if (
            float(expected_eigenvalues[0]) < -_REALIZABILITY_TOL
            or not np.allclose(
                supplied_eigenvalues,
                expected_eigenvalues,
                rtol=0.0,
                atol=_REALIZABILITY_TOL,
            )
        ):
            raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY")
        object.__setattr__(self, "mean", tuple(float(value) for value in mean))
        object.__setattr__(
            self,
            "second_moment",
            tuple(tuple(float(value) for value in row) for row in symmetric),
        )
        object.__setattr__(
            self,
            "eigenvalues",
            tuple(float(value) for value in expected_eigenvalues),
        )
        object.__setattr__(self, "support_identity", support_identity)


def certify_spherical_second_moment(
    *,
    mean: Sequence[float],
    second_moment: Sequence[Sequence[float]],
    support_identity: str,
) -> SphericalSecondMomentCertificate:
    """Certify only the registered zero-mean PSD trace-one moment cone."""

    mean_array = np.asarray(_vector3(mean, "mean"), dtype=float)
    try:
        matrix = np.asarray(second_moment, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY") from exc
    if (
        matrix.shape != (3, 3)
        or not np.all(np.isfinite(matrix))
        or not np.allclose(matrix, matrix.T, rtol=0.0, atol=_REALIZABILITY_TOL)
        or np.linalg.norm(mean_array) > _REALIZABILITY_TOL
        or not math.isclose(
            float(np.trace(matrix)), 1.0, rel_tol=0.0, abs_tol=_REALIZABILITY_TOL
        )
    ):
        raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY")
    symmetric = 0.5 * (matrix + matrix.T)
    eigenvalues = np.linalg.eigvalsh(symmetric)
    if float(eigenvalues[0]) < -_REALIZABILITY_TOL:
        raise DirectionalBridgeError("BLOCKED_MOMENT_REALIZABILITY")
    support_identity = _content_identity(support_identity, "support_identity")
    return SphericalSecondMomentCertificate(
        mean=tuple(float(value) for value in mean_array),
        second_moment=tuple(
            tuple(float(value) for value in row) for row in symmetric
        ),
        eigenvalues=tuple(float(value) for value in eigenvalues),
        support_identity=support_identity,
    )


@dataclass(frozen=True)
class MesDirectionalState:
    """Active-anchor observer-space moments with amplitude/shape separation."""

    state_identity: str
    estimator_identity: str
    field_identity: str
    covariance_identity: str
    transfer_identity: str
    direction_frame: str
    direction_convention: DirectionConvention
    field_quantity: str
    field_units: str
    field_bandlimit: int
    design_condition_number: float
    max_design_condition_number: float
    directional_semantics_status: str
    anchor_id: str
    anchor_value: float
    anchor_channel_key: tuple[str, ...]
    anchor_conditioning: AnchorConditioning
    field_parity: DirectionalFieldParity
    vector_representation: VectorO3Representation
    tensor_representation: TensorO3Representation
    raw_dipole: tuple[float, float, float]
    raw_stf2: tuple[tuple[float, float, float], ...]
    mes_dipole: tuple[float, float, float]
    mes_stf2: tuple[tuple[float, float, float], ...]
    mes_dipole_amplitude: float
    mes_stf2_amplitude: float
    dipole_shape: tuple[float, float, float] | None
    stf2_shape: tuple[tuple[float, float, float], ...] | None
    realizability_status: str
    methodology_role: str = _OBSERVER_ROLE
    directional_support_status: str = "DIRECTION_INDEXED_SUPPORT_BOUND"
    claim_tier: str = "diagnostic_only"
    observer_space_only: bool = True
    physical_response_bound: bool = False
    independent_information_gain: bool = False
    family_identification_status: str = "BLOCKED_PRE_NATIVE_ATLAS"

    def __post_init__(self) -> None:
        estimator_identity = _content_identity(
            self.estimator_identity, "estimator_identity"
        )
        field_identity = _content_identity(self.field_identity, "field_identity")
        covariance_identity = _content_identity(
            self.covariance_identity, "covariance_identity"
        )
        transfer_identity = _content_identity(
            self.transfer_identity, "transfer_identity"
        )
        direction_frame = _required_text(self.direction_frame, "direction_frame")
        if self.direction_convention is not DirectionConvention.RIGHT_HANDED_ACTIVE_O3:
            raise DirectionalBridgeError(
                "direction_convention must be RIGHT_HANDED_ACTIVE_O3"
            )
        field_quantity = _required_text(self.field_quantity, "field_quantity")
        if self.field_units != "dimensionless":
            raise DirectionalBridgeError(
                "field_units must be dimensionless for an MES anchor coordinate"
            )
        if (
            isinstance(self.field_bandlimit, bool)
            or not isinstance(self.field_bandlimit, int)
            or not 0 <= self.field_bandlimit <= 2
        ):
            raise DirectionalBridgeError(
                "BLOCKED_DIRECTIONAL_LEAKAGE: field_bandlimit must be in [0, 2]"
            )
        design_condition = _finite_real(
            self.design_condition_number, "design_condition_number"
        )
        maximum_condition = _finite_real(
            self.max_design_condition_number, "max_design_condition_number"
        )
        if (
            design_condition < 1.0
            or maximum_condition != MAX_DIRECTIONAL_DESIGN_CONDITION
            or design_condition > maximum_condition
        ):
            raise DirectionalBridgeError(
                "BLOCKED_DIRECTIONAL_SUPPORT: directional design is ill-conditioned"
            )
        if self.directional_semantics_status != _DIRECTIONAL_SEMANTICS_STATUS:
            raise DirectionalBridgeError(
                "directional bandlimit/parity semantics cannot be self-promoted"
            )
        anchor_id = _required_text(self.anchor_id, "anchor_id")
        anchor_value = _finite_real(self.anchor_value, "anchor_value")
        if anchor_value <= 0.0:
            raise DirectionalBridgeError("anchor_value must be positive")
        if (
            not isinstance(self.anchor_channel_key, tuple)
            or not self.anchor_channel_key
        ):
            raise DirectionalBridgeError("anchor_channel_key must be a non-empty tuple")
        channel_key = tuple(
            _required_text(item, "anchor_channel_key")
            for item in self.anchor_channel_key
        )
        if not isinstance(self.anchor_conditioning, AnchorConditioning):
            raise DirectionalBridgeError(
                "anchor_conditioning must be an AnchorConditioning"
            )
        anchor_conditioning = self.anchor_conditioning
        if not isinstance(self.field_parity, DirectionalFieldParity):
            raise DirectionalBridgeError(
                "field_parity must be a DirectionalFieldParity"
            )
        expected_vector, expected_tensor = _representations(self.field_parity)
        if (
            self.vector_representation is not expected_vector
            or self.tensor_representation is not expected_tensor
        ):
            raise DirectionalBridgeError("O3 representation does not match field parity")

        raw_vector = np.asarray(_vector3(self.raw_dipole, "raw_dipole"))
        raw_tensor = np.asarray(_stf2(self.raw_stf2, "raw_stf2"))
        mes_vector = np.asarray(_vector3(self.mes_dipole, "mes_dipole"))
        mes_tensor = np.asarray(_stf2(self.mes_stf2, "mes_stf2"))
        scale = max(
            1.0,
            float(np.linalg.norm(raw_vector)),
            float(np.linalg.norm(raw_tensor)),
        )
        if (
            not np.allclose(
                mes_vector * anchor_value,
                raw_vector,
                rtol=2e-14,
                atol=2e-14 * scale,
            )
            or not np.allclose(
                mes_tensor * anchor_value,
                raw_tensor,
                rtol=2e-14,
                atol=2e-14 * scale,
            )
        ):
            raise DirectionalBridgeError("MES moments do not match anchor scaling")
        vector_amplitude, vector_shape = _shape(mes_vector)
        tensor_amplitude, tensor_shape = _shape(mes_tensor)
        if not math.isclose(
            _finite_real(self.mes_dipole_amplitude, "mes_dipole_amplitude"),
            vector_amplitude,
            rel_tol=2e-14,
            abs_tol=2e-14,
        ):
            raise DirectionalBridgeError("MES dipole amplitude is inconsistent")
        if not math.isclose(
            _finite_real(self.mes_stf2_amplitude, "mes_stf2_amplitude"),
            tensor_amplitude,
            rel_tol=2e-14,
            abs_tol=2e-14,
        ):
            raise DirectionalBridgeError("MES STF amplitude is inconsistent")
        supplied_vector_shape = (
            None
            if self.dipole_shape is None
            else _vector3(self.dipole_shape, "dipole_shape")
        )
        supplied_tensor_shape = (
            None
            if self.stf2_shape is None
            else _stf2(self.stf2_shape, "stf2_shape")
        )
        if (
            (vector_shape is None) != (supplied_vector_shape is None)
            or (
                vector_shape is not None
                and not np.allclose(
                    supplied_vector_shape,
                    vector_shape,
                    rtol=0.0,
                    atol=2e-14,
                )
            )
            or (tensor_shape is None) != (supplied_tensor_shape is None)
            or (
                tensor_shape is not None
                and not np.allclose(
                    supplied_tensor_shape,
                    tensor_shape,
                    rtol=0.0,
                    atol=2e-14,
                )
            )
        ):
            raise DirectionalBridgeError("MES normalized shape is inconsistent")

        if self.realizability_status != "SIGNED_FIELD_NOT_A_PROBABILITY_MEASURE":
            raise DirectionalBridgeError(
                "directional state cannot claim a probability-measure certificate"
            )
        if (
            self.methodology_role != _OBSERVER_ROLE
            or self.directional_support_status != "DIRECTION_INDEXED_SUPPORT_BOUND"
            or self.claim_tier != "diagnostic_only"
            or self.observer_space_only is not True
            or self.physical_response_bound is not False
            or self.independent_information_gain is not False
            or self.family_identification_status != "BLOCKED_PRE_NATIVE_ATLAS"
        ):
            raise DirectionalBridgeError("observer-space MES claim boundary drifted")
        expected_identity = _directional_state_identity(
            estimator_identity=estimator_identity,
            field_identity=field_identity,
            covariance_identity=covariance_identity,
            transfer_identity=transfer_identity,
            direction_frame=direction_frame,
            direction_convention=self.direction_convention,
            field_quantity=field_quantity,
            field_units=self.field_units,
            field_bandlimit=self.field_bandlimit,
            design_condition_number=design_condition,
            max_design_condition_number=maximum_condition,
            directional_semantics_status=self.directional_semantics_status,
            anchor_id=anchor_id,
            anchor_value=anchor_value,
            anchor_channel_key=channel_key,
            anchor_conditioning=anchor_conditioning,
            field_parity=self.field_parity,
            raw_dipole=raw_vector,
            raw_stf2=raw_tensor,
        )
        if self.state_identity != expected_identity:
            raise DirectionalBridgeError("state_identity does not bind state content")

        object.__setattr__(self, "estimator_identity", estimator_identity)
        object.__setattr__(self, "field_identity", field_identity)
        object.__setattr__(self, "covariance_identity", covariance_identity)
        object.__setattr__(self, "transfer_identity", transfer_identity)
        object.__setattr__(self, "direction_frame", direction_frame)
        object.__setattr__(self, "field_quantity", field_quantity)
        object.__setattr__(self, "design_condition_number", design_condition)
        object.__setattr__(self, "max_design_condition_number", maximum_condition)
        object.__setattr__(self, "anchor_id", anchor_id)
        object.__setattr__(self, "anchor_value", anchor_value)
        object.__setattr__(self, "anchor_channel_key", channel_key)
        object.__setattr__(self, "anchor_conditioning", anchor_conditioning)
        object.__setattr__(self, "raw_dipole", tuple(float(v) for v in raw_vector))
        object.__setattr__(
            self,
            "raw_stf2",
            tuple(tuple(float(v) for v in row) for row in raw_tensor),
        )
        object.__setattr__(self, "mes_dipole", tuple(float(v) for v in mes_vector))
        object.__setattr__(
            self,
            "mes_stf2",
            tuple(tuple(float(v) for v in row) for row in mes_tensor),
        )
        object.__setattr__(self, "mes_dipole_amplitude", vector_amplitude)
        object.__setattr__(self, "mes_stf2_amplitude", tensor_amplitude)
        object.__setattr__(self, "dipole_shape", vector_shape)
        object.__setattr__(self, "stf2_shape", tensor_shape)

    def as_payload(self) -> dict[str, object]:
        return {
            "format": "HTT_MES_DIRECTIONAL_STATE_V1",
            "state_identity": self.state_identity,
            "estimator_identity": self.estimator_identity,
            "field_identity": self.field_identity,
            "covariance_identity": self.covariance_identity,
            "transfer_identity": self.transfer_identity,
            "direction_frame": self.direction_frame,
            "direction_convention": self.direction_convention.value,
            "field_quantity": self.field_quantity,
            "field_units": self.field_units,
            "field_bandlimit": self.field_bandlimit,
            "design_condition_number": self.design_condition_number,
            "max_design_condition_number": self.max_design_condition_number,
            "directional_semantics_status": self.directional_semantics_status,
            "anchor_id": self.anchor_id,
            "anchor_value": self.anchor_value,
            "anchor_channel_key": list(self.anchor_channel_key),
            "anchor_conditioning": self.anchor_conditioning.value,
            "field_parity": self.field_parity.value,
            "vector_representation": self.vector_representation.value,
            "tensor_representation": self.tensor_representation.value,
            "raw_dipole": list(self.raw_dipole),
            "raw_stf2": [list(row) for row in self.raw_stf2],
            "mes_dipole": list(self.mes_dipole),
            "mes_stf2": [list(row) for row in self.mes_stf2],
            "mes_dipole_amplitude": self.mes_dipole_amplitude,
            "mes_stf2_amplitude": self.mes_stf2_amplitude,
            "dipole_shape": (
                None if self.dipole_shape is None else list(self.dipole_shape)
            ),
            "stf2_shape": (
                None
                if self.stf2_shape is None
                else [list(row) for row in self.stf2_shape]
            ),
            "realizability_status": self.realizability_status,
            "methodology_role": self.methodology_role,
            "directional_support_status": self.directional_support_status,
            "claim_tier": self.claim_tier,
            "observer_space_only": self.observer_space_only,
            "physical_response_bound": self.physical_response_bound,
            "independent_information_gain": self.independent_information_gain,
            "family_identification_status": self.family_identification_status,
            "physical_stress_readiness": (
                PhysicalStressReadiness.BLOCKED_PHYSICAL_RESPONSE_REQUIRED.value
            ),
        }


def _shape(array: np.ndarray) -> tuple[float, object | None]:
    amplitude = float(np.linalg.norm(array))
    if amplitude <= _ZERO_SHAPE_TOL:
        return amplitude, None
    normalized = array / amplitude
    if normalized.ndim == 1:
        return amplitude, tuple(float(value) for value in normalized)
    return amplitude, tuple(
        tuple(float(value) for value in row) for row in normalized
    )


def _directional_state_identity(
    *,
    estimator_identity: str,
    field_identity: str,
    covariance_identity: str,
    transfer_identity: str,
    direction_frame: str,
    direction_convention: DirectionConvention,
    field_quantity: str,
    field_units: str,
    field_bandlimit: int,
    design_condition_number: float,
    max_design_condition_number: float,
    directional_semantics_status: str,
    anchor_id: str,
    anchor_value: float,
    anchor_channel_key: tuple[str, ...],
    anchor_conditioning: AnchorConditioning,
    field_parity: DirectionalFieldParity,
    raw_dipole: np.ndarray,
    raw_stf2: np.ndarray,
) -> str:
    return _canonical_identity(
        {
            "estimator_identity": estimator_identity,
            "field_identity": field_identity,
            "covariance_identity": covariance_identity,
            "transfer_identity": transfer_identity,
            "direction_frame": direction_frame,
            "direction_convention": direction_convention.value,
            "field_quantity": field_quantity,
            "field_units": field_units,
            "field_bandlimit": field_bandlimit,
            "design_condition_number_float_hex": design_condition_number.hex(),
            "max_design_condition_number_float_hex": (
                max_design_condition_number.hex()
            ),
            "directional_semantics_status": directional_semantics_status,
            "anchor_id": anchor_id,
            "anchor_value_float_hex": anchor_value.hex(),
            "anchor_channel_key": anchor_channel_key,
            "anchor_conditioning": anchor_conditioning.value,
            "field_parity": field_parity.value,
            "raw_dipole_float_hex": [float(value).hex() for value in raw_dipole],
            "raw_stf2_float_hex": [
                [float(value).hex() for value in row] for row in raw_stf2
            ],
        },
        role="observer_space_mes_directional_state",
    )


def build_mes_directional_state(
    *,
    directional_moments: DirectionalMomentEstimate,
    anchor: MESAnchorSpec,
) -> MesDirectionalState:
    """Normalize genuine directional moments by one active positive anchor."""

    if type(directional_moments) is not DirectionalMomentEstimate:
        raise DirectionalBridgeError(_SCALAR_REFUSAL)
    if (
        type(anchor) is not MESAnchorSpec
        or anchor.status is not AnchorStatus.VERIFIED
        or not anchor.normalization_allowed
        or anchor.value is None
        or anchor.value <= 0.0
    ):
        raise DirectionalBridgeError("active positive typed MES anchor is required")

    raw_vector = np.asarray(directional_moments.dipole, dtype=float)
    raw_tensor = np.asarray(directional_moments.stf2, dtype=float)
    mes_vector = raw_vector / anchor.value
    mes_tensor = raw_tensor / anchor.value
    vector_amplitude, vector_shape = _shape(mes_vector)
    tensor_amplitude, tensor_shape = _shape(mes_tensor)
    state_identity = _directional_state_identity(
        estimator_identity=directional_moments.estimator_identity,
        field_identity=directional_moments.field_identity,
        covariance_identity=directional_moments.covariance_identity,
        transfer_identity=directional_moments.transfer_identity,
        direction_frame=directional_moments.direction_frame,
        direction_convention=directional_moments.direction_convention,
        field_quantity=directional_moments.field_quantity,
        field_units=directional_moments.field_units,
        field_bandlimit=directional_moments.field_bandlimit,
        design_condition_number=directional_moments.design_condition_number,
        max_design_condition_number=(
            directional_moments.max_design_condition_number
        ),
        directional_semantics_status=(
            directional_moments.directional_semantics_status
        ),
        anchor_id=anchor.anchor_id,
        anchor_value=anchor.value,
        anchor_channel_key=anchor.channel_key,
        anchor_conditioning=anchor.conditioning,
        field_parity=directional_moments.field_parity,
        raw_dipole=raw_vector,
        raw_stf2=raw_tensor,
    )
    return MesDirectionalState(
        state_identity=state_identity,
        estimator_identity=directional_moments.estimator_identity,
        field_identity=directional_moments.field_identity,
        covariance_identity=directional_moments.covariance_identity,
        transfer_identity=directional_moments.transfer_identity,
        direction_frame=directional_moments.direction_frame,
        direction_convention=directional_moments.direction_convention,
        field_quantity=directional_moments.field_quantity,
        field_units=directional_moments.field_units,
        field_bandlimit=directional_moments.field_bandlimit,
        design_condition_number=directional_moments.design_condition_number,
        max_design_condition_number=(
            directional_moments.max_design_condition_number
        ),
        directional_semantics_status=(
            directional_moments.directional_semantics_status
        ),
        anchor_id=anchor.anchor_id,
        anchor_value=anchor.value,
        anchor_channel_key=anchor.channel_key,
        anchor_conditioning=anchor.conditioning,
        field_parity=directional_moments.field_parity,
        vector_representation=directional_moments.vector_representation,
        tensor_representation=directional_moments.tensor_representation,
        raw_dipole=directional_moments.dipole,
        raw_stf2=directional_moments.stf2,
        mes_dipole=tuple(float(value) for value in mes_vector),
        mes_stf2=tuple(tuple(float(value) for value in row) for row in mes_tensor),
        mes_dipole_amplitude=vector_amplitude,
        mes_stf2_amplitude=tensor_amplitude,
        dipole_shape=vector_shape,
        stf2_shape=tensor_shape,
        realizability_status=directional_moments.realizability_status,
    )


def assess_physical_stress_readiness(
    state: MesDirectionalState,
    *,
    response_identity: str | None = None,
    response_channel_key: Sequence[str] | None = None,
) -> PhysicalStressReadiness:
    """Refuse physical stress until a response and numerator are supplied."""

    if type(state) is not MesDirectionalState:
        raise DirectionalBridgeError("typed MesDirectionalState is required")
    if response_identity is None and response_channel_key is None:
        return PhysicalStressReadiness.BLOCKED_PHYSICAL_RESPONSE_REQUIRED
    if response_identity is None or response_channel_key is None:
        raise DirectionalBridgeError("physical response identity and channel are joint")
    _content_identity(response_identity, "response_identity")
    if isinstance(response_channel_key, (str, bytes)):
        raise DirectionalBridgeError("response_channel_key must be a sequence of fields")
    normalized_key = tuple(
        _required_text(item, "response_channel_key")
        for item in response_channel_key
    )
    if normalized_key != state.anchor_channel_key:
        return PhysicalStressReadiness.BLOCKED_CHANNEL_MATCH
    return PhysicalStressReadiness.RESPONSE_BOUND_NUMERATOR_REQUIRED


__all__ = [
    "DirectionalBridgeError",
    "DirectionalEstimatorKind",
    "DirectionalFieldParity",
    "DirectionConvention",
    "DirectionalMomentEstimate",
    "MesDirectionalState",
    "MAX_DIRECTIONAL_DESIGN_CONDITION",
    "PhysicalStressReadiness",
    "SphericalSecondMomentCertificate",
    "TensorO3Representation",
    "VectorO3Representation",
    "assess_physical_stress_readiness",
    "build_mes_directional_state",
    "certify_spherical_second_moment",
    "make_directional_moment_estimate",
]

"""Typed premise-anchor geometry and purpose-specific normalizer benchmarks.

This module treats an anchor as a declared mathematical body, not as a
probability, distance to FLRW, source classifier, or evidence term.  It
implements only runtime classes whose absorbing/convex structure can be
checked directly:

* products of Euclidean block balls;
* positive-definite ellipsoids; and
* bounded centrally symmetric H-polytopes.

Finite conditional families return a gauge interval.  A continuous nuisance
family requires a registered optimizer, and a non-convex union exposes only
conditional component gauges; neither receives a fabricated single gauge.

The benchmark layer compares invertible coordinate normalizations on the same
registered base draws by purpose-specific Pareto fronts.  It has no universal
score and never reports coordinate scaling as information gain.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Integral, Real
from typing import Iterable, Sequence

import numpy as np


class AnchorGeometryError(ValueError):
    """Raised when an anchor or normalizer contract is incomplete."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class AnchorGeometryKind(_StringEnum):
    PRODUCT_BLOCK_BALL = "PRODUCT_BLOCK_BALL"
    ELLIPSOID = "ELLIPSOID"
    POLYTOPE = "POLYTOPE"


class AnchorAvailability(_StringEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    WITHHELD = "WITHHELD"


class AnchorFamilyKind(_StringEnum):
    SINGLE_BODY = "SINGLE_BODY"
    FINITE_CONDITIONAL = "FINITE_CONDITIONAL"
    CONTINUOUS_CONDITIONAL = "CONTINUOUS_CONDITIONAL"
    NONCONVEX_UNION = "NONCONVEX_UNION"


class AnchorGaugeStatus(_StringEnum):
    DEFINED = "DEFINED"
    FINITE_CONDITIONAL = "FINITE_CONDITIONAL"
    OPTIMIZER_REQUIRED = "OPTIMIZER_REQUIRED"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    NONCONVEX_CONDITIONAL_ONLY = "NONCONVEX_CONDITIONAL_ONLY"


class MarginIntervalStatus(_StringEnum):
    FINITE = "FINITE"
    UPPER_UNBOUNDED = "UPPER_UNBOUNDED"
    POSITIVE_INFINITY = "POSITIVE_INFINITY"


class AnchorMarginStatus(_StringEnum):
    DEFINED = "DEFINED"
    CONDITIONAL_INTERVAL = "CONDITIONAL_INTERVAL"
    UNAVAILABLE = "UNAVAILABLE"


class NormalizerPurpose(_StringEnum):
    PREMISE_STRESS = "PREMISE_STRESS"
    RESPONSE_CONDITIONING = "RESPONSE_CONDITIONING"
    PARTIAL_IDENTIFICATION = "PARTIAL_IDENTIFICATION"
    SOURCE_SCREENING = "SOURCE_SCREENING"
    PORTABILITY = "PORTABILITY"


class NormalizerKind(_StringEnum):
    EXPANSION_NORMALIZED = "EXPANSION_NORMALIZED"
    MES_ANCHORED = "MES_ANCHORED"
    FISHER_WHITENED = "FISHER_WHITENED"
    TEMPLATE_LIMIT = "TEMPLATE_LIMIT"
    DYNAMICAL_BREAKDOWN = "DYNAMICAL_BREAKDOWN"
    PRIOR_QUANTILE = "PRIOR_QUANTILE"


class NormalizerAvailability(_StringEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class MetricDirection(_StringEnum):
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"


class NormalizerEvaluationStatus(_StringEnum):
    EVALUATED = "EVALUATED"
    UNAVAILABLE = "UNAVAILABLE"


class DenominatorZeroStatus(_StringEnum):
    FAIL_CLOSED = "FAIL_CLOSED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MesBenchmarkDisposition(_StringEnum):
    PRIMARY_FOR_REGISTERED_PURPOSES = "PRIMARY_FOR_REGISTERED_PURPOSES"
    ONE_ANCHOR_AMONG_FAMILY = "ONE_ANCHOR_AMONG_FAMILY"
    UNAVAILABLE = "UNAVAILABLE"


class ScalingInvarianceStatus(_StringEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class ConjectureDisposition(_StringEnum):
    REFUTED_OR_RESTRICTED = "REFUTED_OR_RESTRICTED"


_ANCHOR_ALLOWED_USE = (
    "typed premise-stress diagnostic",
    "purpose-specific normalization comparison",
)
_ANCHOR_FORBIDDEN_USE = (
    "FLRW converse or proximity",
    "source or Bianchi family identification",
    "probability or evidence",
)
_BENCHMARK_ALLOWED_USE = (
    "purpose-specific Pareto comparison",
    "coordinate-conditioning diagnostic",
)
_BENCHMARK_FORBIDDEN_USE = (
    "universal normalizer winner score",
    "information gain from invertible scaling",
    "FLRW departure or family-identification claim",
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AnchorGeometryError(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Iterable[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise AnchorGeometryError(f"{name} must be a sequence of text")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise AnchorGeometryError(f"{name} must not be empty")
    if len(set(out)) != len(out):
        raise AnchorGeometryError(f"{name} must not contain duplicates")
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise AnchorGeometryError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise AnchorGeometryError(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise AnchorGeometryError(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise AnchorGeometryError(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise AnchorGeometryError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise AnchorGeometryError(f"{name} must be non-negative")
    return out


def _positive(value: object, name: str) -> float:
    out = _nonnegative(value, name)
    if out == 0.0:
        raise AnchorGeometryError(f"{name} must be positive")
    return out


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise AnchorGeometryError(f"{name} must be an integer")
    out = int(value)
    if out < minimum:
        raise AnchorGeometryError(f"{name} must be at least {minimum}")
    return out


def _contains_invalid_scalar(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, (complex, np.complexfloating)):
        return True
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        return True
    if isinstance(value, np.ndarray) and value.dtype.kind in {"b", "c", "O", "S", "U"}:
        return True
    if isinstance(value, (tuple, list)):
        return any(_contains_invalid_scalar(item) for item in value)
    return False


def _array(
    value: object,
    name: str,
    *,
    ndim: int | None = None,
    shape: tuple[int, ...] | None = None,
) -> np.ndarray:
    if _contains_invalid_scalar(value):
        raise AnchorGeometryError(
            f"{name} must contain finite real numeric values, not bool/text/complex"
        )
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise AnchorGeometryError(f"{name} must be numeric") from exc
    if ndim is not None and out.ndim != ndim:
        raise AnchorGeometryError(f"{name} must have ndim={ndim}")
    if shape is not None and out.shape != shape:
        raise AnchorGeometryError(
            f"{name} must have shape {shape}, got {out.shape}"
        )
    if out.size == 0:
        raise AnchorGeometryError(f"{name} must not be empty")
    if not np.isfinite(out).all():
        raise AnchorGeometryError(f"{name} must be finite")
    return out


def _matrix_tuple(value: object, name: str, dimension: int) -> tuple[tuple[float, ...], ...]:
    out = _array(value, name, ndim=2, shape=(dimension, dimension))
    return tuple(tuple(float(item) for item in row) for row in out)


def _sha256_identity(value: object, name: str) -> str:
    out = _text(value, name)
    prefix = "sha256:"
    digest = out[len(prefix) :] if out.startswith(prefix) else ""
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise AnchorGeometryError(
            f"{name} must be a lowercase sha256 content identity"
        )
    return out


@dataclass(frozen=True)
class AnchorVector:
    """A vector whose channel metadata must match its anchor exactly."""

    vector_id: str
    coordinate_labels: tuple[str, ...]
    values: tuple[float, ...]
    frame: str
    normalization: str
    perturbative_order: str
    branch: str

    def __post_init__(self) -> None:
        _text(self.vector_id, "vector_id")
        labels = _texts(self.coordinate_labels, "coordinate_labels")
        values = tuple(
            _real(value, f"values[{index}]")
            for index, value in enumerate(self.values)
        )
        if len(values) != len(labels):
            raise AnchorGeometryError(
                "values and coordinate_labels must have the same length"
            )
        object.__setattr__(self, "coordinate_labels", labels)
        object.__setattr__(self, "values", values)
        for name in ("frame", "normalization", "perturbative_order", "branch"):
            _text(getattr(self, name), name)


@dataclass(frozen=True)
class AnchorBlockSpec:
    """One Euclidean block in a product-of-block-balls anchor."""

    block_id: str
    coordinate_indices: tuple[int, ...]
    radius: float | None
    availability: AnchorAvailability = AnchorAvailability.AVAILABLE
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.block_id, "block_id")
        if not isinstance(self.availability, AnchorAvailability):
            raise AnchorGeometryError(
                "availability must be an AnchorAvailability"
            )
        if isinstance(self.coordinate_indices, (str, bytes)):
            raise AnchorGeometryError("coordinate_indices must be integers")
        indices = tuple(
            _integer(value, "coordinate_indices", minimum=0)
            for value in self.coordinate_indices
        )
        if not indices or len(indices) != len(set(indices)):
            raise AnchorGeometryError(
                "coordinate_indices must be non-empty and unique"
            )
        object.__setattr__(self, "coordinate_indices", indices)
        if self.availability is AnchorAvailability.AVAILABLE:
            object.__setattr__(self, "radius", _positive(self.radius, "radius"))
            if self.unavailable_reason is not None:
                raise AnchorGeometryError(
                    "available blocks must not carry unavailable_reason"
                )
        else:
            if self.radius is not None:
                raise AnchorGeometryError(
                    "missing or withheld blocks must not carry a numeric radius"
                )
            _text(self.unavailable_reason, "unavailable_reason")


@dataclass(frozen=True)
class PolytopeHalfspace:
    """One halfspace ``normal dot u <= bound``."""

    normal: tuple[float, ...]
    bound: float

    def __post_init__(self) -> None:
        normal = tuple(
            _real(value, f"normal[{index}]")
            for index, value in enumerate(self.normal)
        )
        if not normal or np.linalg.norm(normal) == 0.0:
            raise AnchorGeometryError("halfspace normal must be nonzero")
        object.__setattr__(self, "normal", normal)
        object.__setattr__(self, "bound", _positive(self.bound, "bound"))


@dataclass(frozen=True)
class AnchorBodySpec:
    """One typed convex absorbing body in a fixed coordinate channel."""

    body_id: str
    geometry: AnchorGeometryKind
    coordinate_labels: tuple[str, ...]
    frame: str
    normalization: str
    perturbative_order: str
    branch: str
    premise_identity: str
    blocks: tuple[AnchorBlockSpec, ...] = ()
    quadratic_form: tuple[tuple[float, ...], ...] = ()
    halfspaces: tuple[PolytopeHalfspace, ...] = ()
    availability: AnchorAvailability = AnchorAvailability.AVAILABLE
    unavailable_reason: str | None = None
    assumptions: tuple[str, ...] = ()
    allowed_use: tuple[str, ...] = _ANCHOR_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _ANCHOR_FORBIDDEN_USE

    def __post_init__(self) -> None:
        _text(self.body_id, "body_id")
        if not isinstance(self.geometry, AnchorGeometryKind):
            raise AnchorGeometryError(
                "geometry must be an AnchorGeometryKind"
            )
        if not isinstance(self.availability, AnchorAvailability):
            raise AnchorGeometryError(
                "availability must be an AnchorAvailability"
            )
        labels = _texts(self.coordinate_labels, "coordinate_labels")
        object.__setattr__(self, "coordinate_labels", labels)
        for name in (
            "frame",
            "normalization",
            "perturbative_order",
            "branch",
            "premise_identity",
        ):
            _text(getattr(self, name), name)
        object.__setattr__(
            self, "assumptions", _texts(self.assumptions, "assumptions", empty_ok=True)
        )
        object.__setattr__(
            self, "allowed_use", _texts(self.allowed_use, "allowed_use")
        )
        object.__setattr__(
            self, "forbidden_use", _texts(self.forbidden_use, "forbidden_use")
        )
        if self.availability is not AnchorAvailability.AVAILABLE:
            _text(self.unavailable_reason, "unavailable_reason")
            if self.blocks or self.quadratic_form or self.halfspaces:
                raise AnchorGeometryError(
                    "missing or withheld bodies must not expose numeric geometry"
                )
            return
        if self.unavailable_reason is not None:
            raise AnchorGeometryError(
                "available bodies must not carry unavailable_reason"
            )

        dimension = len(labels)
        if self.geometry is AnchorGeometryKind.PRODUCT_BLOCK_BALL:
            if not self.blocks or self.quadratic_form or self.halfspaces:
                raise AnchorGeometryError(
                    "product balls require blocks and no other geometry"
                )
            if any(
                not isinstance(block, AnchorBlockSpec)
                for block in self.blocks
            ):
                raise AnchorGeometryError(
                    "blocks must contain AnchorBlockSpec values"
                )
            block_ids = tuple(block.block_id for block in self.blocks)
            if len(block_ids) != len(set(block_ids)):
                raise AnchorGeometryError(
                    "product-ball block_id values must be unique"
                )
            covered = tuple(
                index for block in self.blocks for index in block.coordinate_indices
            )
            if sorted(covered) != list(range(dimension)):
                raise AnchorGeometryError(
                    "product-ball blocks must cover every coordinate exactly once"
                )
        elif self.geometry is AnchorGeometryKind.ELLIPSOID:
            if self.blocks or self.halfspaces or not self.quadratic_form:
                raise AnchorGeometryError(
                    "ellipsoids require only a quadratic_form"
                )
            quadratic = _array(
                self.quadratic_form,
                "quadratic_form",
                ndim=2,
                shape=(dimension, dimension),
            )
            if not np.allclose(quadratic, quadratic.T, rtol=0.0, atol=1e-12):
                raise AnchorGeometryError("quadratic_form must be symmetric")
            if float(np.min(np.linalg.eigvalsh(quadratic))) <= 0.0:
                raise AnchorGeometryError(
                    "quadratic_form must be positive definite"
                )
            object.__setattr__(
                self,
                "quadratic_form",
                tuple(tuple(float(item) for item in row) for row in quadratic),
            )
        else:
            if self.blocks or self.quadratic_form or not self.halfspaces:
                raise AnchorGeometryError(
                    "polytopes require only halfspaces"
                )
            if any(
                not isinstance(halfspace, PolytopeHalfspace)
                for halfspace in self.halfspaces
            ):
                raise AnchorGeometryError(
                    "halfspaces must contain PolytopeHalfspace values"
                )
            for halfspace in self.halfspaces:
                if len(halfspace.normal) != dimension:
                    raise AnchorGeometryError(
                        "every halfspace normal must match the coordinate dimension"
                    )
            normals = np.asarray(
                [halfspace.normal for halfspace in self.halfspaces],
                dtype=float,
            )
            if int(np.linalg.matrix_rank(normals)) != dimension:
                raise AnchorGeometryError(
                    "polytope normals must span the coordinate space"
                )
            for halfspace in self.halfspaces:
                if not any(
                    other.bound == halfspace.bound
                    and np.allclose(
                        other.normal,
                        -np.asarray(halfspace.normal),
                        rtol=0.0,
                        atol=1e-12,
                    )
                    for other in self.halfspaces
                ):
                    raise AnchorGeometryError(
                        "runtime polytopes must be centrally symmetric"
                    )

    @property
    def channel_key(self) -> tuple[object, ...]:
        return (
            self.coordinate_labels,
            self.frame,
            self.normalization,
            self.perturbative_order,
            self.branch,
        )


@dataclass(frozen=True)
class AnchorFamily:
    """A single, finite, continuous, or explicitly non-convex anchor family."""

    family_id: str
    kind: AnchorFamilyKind
    bodies: tuple[AnchorBodySpec, ...] = ()
    nuisance_identity: str | None = None
    optimizer_contract: str | None = None
    assumptions: tuple[str, ...] = ()
    coordinate_labels: tuple[str, ...] = ()
    frame: str | None = None
    normalization: str | None = None
    perturbative_order: str | None = None
    branch: str | None = None

    def __post_init__(self) -> None:
        _text(self.family_id, "family_id")
        if not isinstance(self.kind, AnchorFamilyKind):
            raise AnchorGeometryError("kind must be an AnchorFamilyKind")
        object.__setattr__(
            self, "assumptions", _texts(self.assumptions, "assumptions", empty_ok=True)
        )
        if any(not isinstance(body, AnchorBodySpec) for body in self.bodies):
            raise AnchorGeometryError(
                "bodies must contain AnchorBodySpec values"
            )
        body_ids = tuple(body.body_id for body in self.bodies)
        if len(body_ids) != len(set(body_ids)):
            raise AnchorGeometryError("anchor family body_id values must be unique")
        if self.kind is AnchorFamilyKind.SINGLE_BODY:
            if len(self.bodies) != 1:
                raise AnchorGeometryError("SINGLE_BODY requires exactly one body")
            if self.nuisance_identity is not None:
                raise AnchorGeometryError(
                    "SINGLE_BODY must not carry nuisance_identity"
                )
        elif self.kind is AnchorFamilyKind.FINITE_CONDITIONAL:
            if not self.bodies:
                raise AnchorGeometryError(
                    "FINITE_CONDITIONAL requires at least one body"
                )
            _text(self.nuisance_identity, "nuisance_identity")
        elif self.kind is AnchorFamilyKind.CONTINUOUS_CONDITIONAL:
            if self.bodies:
                raise AnchorGeometryError(
                    "continuous families must not contain a hidden discretization"
                )
            _text(self.nuisance_identity, "nuisance_identity")
            _text(self.optimizer_contract, "optimizer_contract")
        else:
            if len(self.bodies) < 2:
                raise AnchorGeometryError(
                    "NONCONVEX_UNION requires at least two conditional bodies"
                )
            _text(self.nuisance_identity, "nuisance_identity")
        if self.kind is AnchorFamilyKind.CONTINUOUS_CONDITIONAL:
            labels = _texts(self.coordinate_labels, "coordinate_labels")
            object.__setattr__(self, "coordinate_labels", labels)
            for name in (
                "frame",
                "normalization",
                "perturbative_order",
                "branch",
            ):
                _text(getattr(self, name), name)
            return
        if self.optimizer_contract is not None:
            raise AnchorGeometryError(
                "only CONTINUOUS_CONDITIONAL may carry optimizer_contract"
            )
        channel_keys = {body.channel_key for body in self.bodies}
        if len(channel_keys) != 1:
            raise AnchorGeometryError(
                "all bodies in an anchor family must share one typed channel"
            )
        labels, frame, normalization, order, branch = next(iter(channel_keys))
        explicit_channel = (
            self.coordinate_labels,
            self.frame,
            self.normalization,
            self.perturbative_order,
            self.branch,
        )
        if any(
            value not in ((), None)
            for value in explicit_channel
        ) and explicit_channel != (
            labels,
            frame,
            normalization,
            order,
            branch,
        ):
            raise AnchorGeometryError(
                "explicit family channel metadata must match its bodies"
            )
        object.__setattr__(self, "coordinate_labels", labels)
        object.__setattr__(self, "frame", frame)
        object.__setattr__(self, "normalization", normalization)
        object.__setattr__(self, "perturbative_order", order)
        object.__setattr__(self, "branch", branch)

    @property
    def channel_key(self) -> tuple[object, ...]:
        return (
            self.coordinate_labels,
            self.frame,
            self.normalization,
            self.perturbative_order,
            self.branch,
        )


@dataclass(frozen=True)
class AnchorGaugeInterval:
    """Gauge or conditional gauge interval; never a probability or evidence."""

    anchor_id: str
    vector_id: str
    lower: float | None
    upper: float | None
    status: AnchorGaugeStatus
    conditional_values: tuple[tuple[str, float], ...] = ()
    assumptions: tuple[str, ...] = ()
    allowed_use: tuple[str, ...] = _ANCHOR_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _ANCHOR_FORBIDDEN_USE

    def __post_init__(self) -> None:
        _text(self.anchor_id, "anchor_id")
        _text(self.vector_id, "vector_id")
        if not isinstance(self.status, AnchorGaugeStatus):
            raise AnchorGeometryError("status must be an AnchorGaugeStatus")
        object.__setattr__(
            self, "assumptions", _texts(self.assumptions, "assumptions", empty_ok=True)
        )
        object.__setattr__(
            self, "allowed_use", _texts(self.allowed_use, "allowed_use")
        )
        object.__setattr__(
            self, "forbidden_use", _texts(self.forbidden_use, "forbidden_use")
        )
        values = tuple(
            (_text(name, "conditional_values.name"), _nonnegative(value, "conditional_values.value"))
            for name, value in self.conditional_values
        )
        if len({name for name, _ in values}) != len(values):
            raise AnchorGeometryError(
                "conditional_values must not contain duplicate names"
            )
        object.__setattr__(self, "conditional_values", values)
        numeric_statuses = {
            AnchorGaugeStatus.DEFINED,
            AnchorGaugeStatus.FINITE_CONDITIONAL,
            AnchorGaugeStatus.NONCONVEX_CONDITIONAL_ONLY,
        }
        if self.status in numeric_statuses:
            lower = _nonnegative(self.lower, "lower")
            upper = _nonnegative(self.upper, "upper")
            if lower > upper:
                raise AnchorGeometryError("lower must not exceed upper")
            if not values:
                raise AnchorGeometryError(
                    "numeric gauge reports require conditional_values"
                )
            conditional_numbers = tuple(value for _, value in values)
            if lower != min(conditional_numbers) or upper != max(
                conditional_numbers
            ):
                raise AnchorGeometryError(
                    "gauge interval endpoints must equal the extrema of "
                    "conditional_values"
                )
            if self.status is AnchorGaugeStatus.DEFINED and lower != upper:
                raise AnchorGeometryError(
                    "DEFINED gauge reports must be point identified"
                )
            if (
                self.status is AnchorGaugeStatus.DEFINED
                and len(values) != 1
            ):
                raise AnchorGeometryError(
                    "DEFINED gauge reports require exactly one conditional value"
                )
            object.__setattr__(self, "lower", lower)
            object.__setattr__(self, "upper", upper)
        elif self.lower is not None or self.upper is not None or values:
            raise AnchorGeometryError(
                "non-numeric gauge statuses must not carry numeric values"
            )

    @property
    def point_identified(self) -> bool:
        return (
            self.lower is not None
            and self.upper is not None
            and self.lower == self.upper
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "anchor_id": self.anchor_id,
            "vector_id": self.vector_id,
            "lower": self.lower,
            "upper": self.upper,
            "status": self.status.value,
            "conditional_values": {
                name: value for name, value in self.conditional_values
            },
            "assumptions": list(self.assumptions),
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


@dataclass(frozen=True)
class _SemanticInterval:
    lower: float | None
    upper: float | None
    status: MarginIntervalStatus

    def __post_init__(self) -> None:
        if not isinstance(self.status, MarginIntervalStatus):
            raise AnchorGeometryError(
                "status must be a MarginIntervalStatus"
            )
        if self.status is MarginIntervalStatus.FINITE:
            lower = _real(self.lower, "lower")
            upper = _real(self.upper, "upper")
            if lower > upper:
                raise AnchorGeometryError("lower must not exceed upper")
            object.__setattr__(self, "lower", lower)
            object.__setattr__(self, "upper", upper)
        elif self.status is MarginIntervalStatus.UPPER_UNBOUNDED:
            object.__setattr__(self, "lower", _real(self.lower, "lower"))
            if self.upper is not None:
                raise AnchorGeometryError(
                    "UPPER_UNBOUNDED must carry upper=None"
                )
        elif self.lower is not None or self.upper is not None:
            raise AnchorGeometryError(
                "POSITIVE_INFINITY must carry no finite endpoints"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class AdditiveRadialMargin(_SemanticInterval):
    """The additive radial margin ``1-rho``."""


@dataclass(frozen=True)
class MultiplicativeBoundaryScale(_SemanticInterval):
    """The multiplicative boundary scale ``1/rho``."""


@dataclass(frozen=True)
class RelativeBoundaryGrowth(_SemanticInterval):
    """The relative multiplicative growth ``1/rho - 1``."""


@dataclass(frozen=True)
class RawAnchorExcess(_SemanticInterval):
    """The uncalibrated excess ``max(rho-1, 0)``."""


@dataclass(frozen=True)
class AnchorMarginReport:
    gauge: AnchorGaugeInterval
    additive_radial_margin: AdditiveRadialMargin | None
    multiplicative_boundary_scale: MultiplicativeBoundaryScale | None
    relative_boundary_growth: RelativeBoundaryGrowth | None
    raw_anchor_excess: RawAnchorExcess | None
    status: AnchorMarginStatus
    automatic_evidence_status: str = "FORBIDDEN_REQUIRES_JOINT_NULL_CALIBRATION"

    def __post_init__(self) -> None:
        if not isinstance(self.gauge, AnchorGaugeInterval):
            raise AnchorGeometryError(
                "gauge must be an AnchorGaugeInterval"
            )
        if not isinstance(self.status, AnchorMarginStatus):
            raise AnchorGeometryError("status must be an AnchorMarginStatus")
        fields = (
            self.additive_radial_margin,
            self.multiplicative_boundary_scale,
            self.relative_boundary_growth,
            self.raw_anchor_excess,
        )
        if self.status is AnchorMarginStatus.UNAVAILABLE:
            if any(item is not None for item in fields):
                raise AnchorGeometryError(
                    "unavailable margin reports must not carry numeric intervals"
                )
            if self.gauge.lower is not None or self.gauge.upper is not None:
                raise AnchorGeometryError(
                    "unavailable margin status requires a non-numeric gauge"
                )
        else:
            if any(item is None for item in fields):
                raise AnchorGeometryError(
                    "defined margin reports require all four semantic intervals"
                )
            if self.gauge.lower is None or self.gauge.upper is None:
                raise AnchorGeometryError(
                    "numeric margin status requires a numeric gauge"
                )
            if (
                self.status is AnchorMarginStatus.DEFINED
                and self.gauge.status is not AnchorGaugeStatus.DEFINED
            ):
                raise AnchorGeometryError(
                    "DEFINED margin status requires a single-body gauge"
                )
            if (
                self.status is AnchorMarginStatus.CONDITIONAL_INTERVAL
                and self.gauge.status
                not in {
                    AnchorGaugeStatus.FINITE_CONDITIONAL,
                    AnchorGaugeStatus.NONCONVEX_CONDITIONAL_ONLY,
                }
            ):
                raise AnchorGeometryError(
                    "conditional margin status requires a conditional gauge"
                )
            expected_fields = (
                AdditiveRadialMargin(
                    lower=1.0 - self.gauge.upper,
                    upper=1.0 - self.gauge.lower,
                    status=MarginIntervalStatus.FINITE,
                ),
                _reciprocal_interval(
                    self.gauge.lower,
                    self.gauge.upper,
                    relative=False,
                ),
                _reciprocal_interval(
                    self.gauge.lower,
                    self.gauge.upper,
                    relative=True,
                ),
                RawAnchorExcess(
                    lower=max(self.gauge.lower - 1.0, 0.0),
                    upper=max(self.gauge.upper - 1.0, 0.0),
                    status=MarginIntervalStatus.FINITE,
                ),
            )
            if fields != expected_fields:
                raise AnchorGeometryError(
                    "margin intervals must be derived exactly from the gauge"
                )
        if self.automatic_evidence_status != (
            "FORBIDDEN_REQUIRES_JOINT_NULL_CALIBRATION"
        ):
            raise AnchorGeometryError(
                "raw anchor excess cannot be promoted to automatic evidence"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "gauge": self.gauge.as_payload(),
            "additive_radial_margin": (
                None
                if self.additive_radial_margin is None
                else self.additive_radial_margin.as_payload()
            ),
            "multiplicative_boundary_scale": (
                None
                if self.multiplicative_boundary_scale is None
                else self.multiplicative_boundary_scale.as_payload()
            ),
            "relative_boundary_growth": (
                None
                if self.relative_boundary_growth is None
                else self.relative_boundary_growth.as_payload()
            ),
            "raw_anchor_excess": (
                None
                if self.raw_anchor_excess is None
                else self.raw_anchor_excess.as_payload()
            ),
            "status": self.status.value,
            "automatic_evidence_status": self.automatic_evidence_status,
        }


def _channel_matches(vector: AnchorVector, body: AnchorBodySpec) -> bool:
    return (
        vector.coordinate_labels,
        vector.frame,
        vector.normalization,
        vector.perturbative_order,
        vector.branch,
    ) == body.channel_key


def _body_gauge(body: AnchorBodySpec, vector: AnchorVector) -> AnchorGaugeInterval:
    if not _channel_matches(vector, body):
        return AnchorGaugeInterval(
            anchor_id=body.body_id,
            vector_id=vector.vector_id,
            lower=None,
            upper=None,
            status=AnchorGaugeStatus.CHANNEL_MISMATCH,
            assumptions=body.assumptions,
        )
    if body.availability is not AnchorAvailability.AVAILABLE:
        return AnchorGaugeInterval(
            anchor_id=body.body_id,
            vector_id=vector.vector_id,
            lower=None,
            upper=None,
            status=AnchorGaugeStatus.ANCHOR_UNAVAILABLE,
            assumptions=body.assumptions,
        )
    values = np.asarray(vector.values, dtype=float)
    if body.geometry is AnchorGeometryKind.PRODUCT_BLOCK_BALL:
        if any(
            block.availability is not AnchorAvailability.AVAILABLE
            for block in body.blocks
        ):
            return AnchorGaugeInterval(
                anchor_id=body.body_id,
                vector_id=vector.vector_id,
                lower=None,
                upper=None,
                status=AnchorGaugeStatus.ANCHOR_UNAVAILABLE,
                assumptions=body.assumptions,
            )
        gauge = max(
            float(np.linalg.norm(values[list(block.coordinate_indices)]))
            / float(block.radius)
            for block in body.blocks
        )
    elif body.geometry is AnchorGeometryKind.ELLIPSOID:
        quadratic = np.asarray(body.quadratic_form, dtype=float)
        gauge = math.sqrt(max(float(values @ quadratic @ values), 0.0))
    else:
        gauge = max(
            float(np.dot(halfspace.normal, values)) / halfspace.bound
            for halfspace in body.halfspaces
        )
        gauge = max(gauge, 0.0)
    return AnchorGaugeInterval(
        anchor_id=body.body_id,
        vector_id=vector.vector_id,
        lower=gauge,
        upper=gauge,
        status=AnchorGaugeStatus.DEFINED,
        conditional_values=((body.body_id, gauge),),
        assumptions=body.assumptions,
    )


def evaluate_anchor_gauge(
    anchor: AnchorBodySpec | AnchorFamily,
    vector: AnchorVector,
) -> AnchorGaugeInterval:
    """Evaluate a typed gauge without inventing missing family structure."""

    if isinstance(anchor, AnchorBodySpec):
        return _body_gauge(anchor, vector)
    if not isinstance(anchor, AnchorFamily):
        raise AnchorGeometryError(
            "anchor must be an AnchorBodySpec or AnchorFamily"
        )
    vector_channel = (
        vector.coordinate_labels,
        vector.frame,
        vector.normalization,
        vector.perturbative_order,
        vector.branch,
    )
    if vector_channel != anchor.channel_key:
        return AnchorGaugeInterval(
            anchor_id=anchor.family_id,
            vector_id=vector.vector_id,
            lower=None,
            upper=None,
            status=AnchorGaugeStatus.CHANNEL_MISMATCH,
            assumptions=anchor.assumptions,
        )
    if anchor.kind is AnchorFamilyKind.CONTINUOUS_CONDITIONAL:
        return AnchorGaugeInterval(
            anchor_id=anchor.family_id,
            vector_id=vector.vector_id,
            lower=None,
            upper=None,
            status=AnchorGaugeStatus.OPTIMIZER_REQUIRED,
            assumptions=anchor.assumptions,
        )
    reports = tuple(_body_gauge(body, vector) for body in anchor.bodies)
    if any(report.status is AnchorGaugeStatus.CHANNEL_MISMATCH for report in reports):
        return AnchorGaugeInterval(
            anchor_id=anchor.family_id,
            vector_id=vector.vector_id,
            lower=None,
            upper=None,
            status=AnchorGaugeStatus.CHANNEL_MISMATCH,
            assumptions=anchor.assumptions,
        )
    if any(
        report.status is AnchorGaugeStatus.ANCHOR_UNAVAILABLE
        for report in reports
    ):
        return AnchorGaugeInterval(
            anchor_id=anchor.family_id,
            vector_id=vector.vector_id,
            lower=None,
            upper=None,
            status=AnchorGaugeStatus.ANCHOR_UNAVAILABLE,
            assumptions=anchor.assumptions,
        )
    conditional_values = tuple(
        item
        for report in reports
        for item in report.conditional_values
    )
    values = tuple(value for _, value in conditional_values)
    if anchor.kind is AnchorFamilyKind.SINGLE_BODY:
        status = AnchorGaugeStatus.DEFINED
    elif anchor.kind is AnchorFamilyKind.FINITE_CONDITIONAL:
        status = AnchorGaugeStatus.FINITE_CONDITIONAL
    else:
        status = AnchorGaugeStatus.NONCONVEX_CONDITIONAL_ONLY
    return AnchorGaugeInterval(
        anchor_id=anchor.family_id,
        vector_id=vector.vector_id,
        lower=min(values),
        upper=max(values),
        status=status,
        conditional_values=conditional_values,
        assumptions=anchor.assumptions,
    )


def _reciprocal_interval(
    lower: float,
    upper: float,
    *,
    relative: bool,
) -> MultiplicativeBoundaryScale | RelativeBoundaryGrowth:
    interval_type = RelativeBoundaryGrowth if relative else MultiplicativeBoundaryScale
    shift = 1.0 if relative else 0.0
    if upper == 0.0:
        return interval_type(
            lower=None,
            upper=None,
            status=MarginIntervalStatus.POSITIVE_INFINITY,
        )
    finite_lower = 1.0 / upper - shift
    if lower == 0.0:
        return interval_type(
            lower=finite_lower,
            upper=None,
            status=MarginIntervalStatus.UPPER_UNBOUNDED,
        )
    return interval_type(
        lower=finite_lower,
        upper=1.0 / lower - shift,
        status=MarginIntervalStatus.FINITE,
    )


def build_anchor_margin_report(
    gauge: AnchorGaugeInterval,
) -> AnchorMarginReport:
    """Keep additive margin, multiplicative headroom, and raw excess distinct."""

    if gauge.lower is None or gauge.upper is None:
        return AnchorMarginReport(
            gauge=gauge,
            additive_radial_margin=None,
            multiplicative_boundary_scale=None,
            relative_boundary_growth=None,
            raw_anchor_excess=None,
            status=AnchorMarginStatus.UNAVAILABLE,
        )
    additive = AdditiveRadialMargin(
        lower=1.0 - gauge.upper,
        upper=1.0 - gauge.lower,
        status=MarginIntervalStatus.FINITE,
    )
    multiplicative = _reciprocal_interval(
        gauge.lower, gauge.upper, relative=False
    )
    relative = _reciprocal_interval(
        gauge.lower, gauge.upper, relative=True
    )
    excess = RawAnchorExcess(
        lower=max(gauge.lower - 1.0, 0.0),
        upper=max(gauge.upper - 1.0, 0.0),
        status=MarginIntervalStatus.FINITE,
    )
    status = (
        AnchorMarginStatus.DEFINED
        if gauge.status is AnchorGaugeStatus.DEFINED
        else AnchorMarginStatus.CONDITIONAL_INTERVAL
    )
    return AnchorMarginReport(
        gauge=gauge,
        additive_radial_margin=additive,
        multiplicative_boundary_scale=multiplicative,
        relative_boundary_growth=relative,
        raw_anchor_excess=excess,
        status=status,
    )


@dataclass(frozen=True)
class NormalizerSpec:
    """One purpose-declared invertible coordinate normalization."""

    normalizer_id: str
    kind: NormalizerKind
    purposes: tuple[NormalizerPurpose, ...]
    coordinate_labels: tuple[str, ...]
    coordinate_map: tuple[tuple[float, ...], ...] = ()
    source_identity: str = ""
    assumptions: tuple[str, ...] = ()
    availability: NormalizerAvailability = NormalizerAvailability.AVAILABLE
    unavailable_reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.normalizer_id, "normalizer_id")
        if not isinstance(self.kind, NormalizerKind):
            raise AnchorGeometryError("kind must be a NormalizerKind")
        if not isinstance(self.availability, NormalizerAvailability):
            raise AnchorGeometryError(
                "availability must be a NormalizerAvailability"
            )
        if isinstance(self.purposes, (str, bytes)):
            raise AnchorGeometryError("purposes must be NormalizerPurpose values")
        purposes = tuple(self.purposes)
        if (
            not purposes
            or any(not isinstance(item, NormalizerPurpose) for item in purposes)
            or len(purposes) != len(set(purposes))
        ):
            raise AnchorGeometryError(
                "purposes must be unique NormalizerPurpose values"
            )
        object.__setattr__(self, "purposes", purposes)
        labels = _texts(self.coordinate_labels, "coordinate_labels")
        object.__setattr__(self, "coordinate_labels", labels)
        _text(self.source_identity, "source_identity")
        object.__setattr__(
            self, "assumptions", _texts(self.assumptions, "assumptions", empty_ok=True)
        )
        if self.availability is NormalizerAvailability.AVAILABLE:
            matrix = _matrix_tuple(
                self.coordinate_map, "coordinate_map", len(labels)
            )
            if int(np.linalg.matrix_rank(np.asarray(matrix))) != len(labels):
                raise AnchorGeometryError(
                    "available normalizers require an invertible coordinate_map"
                )
            object.__setattr__(self, "coordinate_map", matrix)
            if self.unavailable_reason is not None:
                raise AnchorGeometryError(
                    "available normalizers must not carry unavailable_reason"
                )
        else:
            if self.coordinate_map:
                raise AnchorGeometryError(
                    "unavailable normalizers must not expose a coordinate map"
                )
            _text(self.unavailable_reason, "unavailable_reason")


@dataclass(frozen=True)
class BenchmarkMetric:
    metric_id: str
    value: float
    direction: MetricDirection
    evidence_identity: str

    def __post_init__(self) -> None:
        _text(self.metric_id, "metric_id")
        object.__setattr__(self, "value", _real(self.value, "value"))
        if not isinstance(self.direction, MetricDirection):
            raise AnchorGeometryError(
                "direction must be a MetricDirection"
            )
        _text(self.evidence_identity, "evidence_identity")


@dataclass(frozen=True)
class NormalizerEvaluation:
    normalizer_id: str
    purpose: NormalizerPurpose
    status: NormalizerEvaluationStatus
    metrics: tuple[BenchmarkMetric, ...]
    rank_before: int | None
    rank_after: int | None
    denominator_zero_status: DenominatorZeroStatus
    likelihood_invariance_error: float | None
    base_draws_receipt: str

    def __post_init__(self) -> None:
        _text(self.normalizer_id, "normalizer_id")
        if not isinstance(self.purpose, NormalizerPurpose):
            raise AnchorGeometryError(
                "purpose must be a NormalizerPurpose"
            )
        if not isinstance(self.status, NormalizerEvaluationStatus):
            raise AnchorGeometryError(
                "status must be a NormalizerEvaluationStatus"
            )
        if not isinstance(self.denominator_zero_status, DenominatorZeroStatus):
            raise AnchorGeometryError(
                "denominator_zero_status must be a DenominatorZeroStatus"
            )
        _sha256_identity(self.base_draws_receipt, "base_draws_receipt")
        metric_ids = tuple(metric.metric_id for metric in self.metrics)
        if len(metric_ids) != len(set(metric_ids)):
            raise AnchorGeometryError("metrics must not contain duplicate IDs")
        if self.status is NormalizerEvaluationStatus.EVALUATED:
            if not self.metrics:
                raise AnchorGeometryError(
                    "evaluated normalizers require at least one metric"
                )
            before = _integer(self.rank_before, "rank_before")
            after = _integer(self.rank_after, "rank_after")
            if before != after:
                raise AnchorGeometryError(
                    "invertible normalization must not change response rank"
                )
            object.__setattr__(self, "rank_before", before)
            object.__setattr__(self, "rank_after", after)
            object.__setattr__(
                self,
                "likelihood_invariance_error",
                _nonnegative(
                    self.likelihood_invariance_error,
                    "likelihood_invariance_error",
                ),
            )
        elif (
            self.metrics
            or self.rank_before is not None
            or self.rank_after is not None
            or self.likelihood_invariance_error is not None
        ):
            raise AnchorGeometryError(
                "unavailable evaluations must not carry synthetic numeric metrics"
            )


@dataclass(frozen=True)
class PurposeParetoFront:
    purpose: NormalizerPurpose
    normalizer_ids: tuple[str, ...]
    metric_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, NormalizerPurpose):
            raise AnchorGeometryError(
                "purpose must be a NormalizerPurpose"
            )
        object.__setattr__(
            self, "normalizer_ids", _texts(self.normalizer_ids, "normalizer_ids")
        )
        object.__setattr__(
            self, "metric_ids", _texts(self.metric_ids, "metric_ids")
        )


@dataclass(frozen=True)
class NormalizerBenchmarkReport:
    specs: tuple[NormalizerSpec, ...]
    evaluations: tuple[NormalizerEvaluation, ...]
    pareto_fronts: tuple[PurposeParetoFront, ...]
    mes_disposition: MesBenchmarkDisposition
    base_draws_receipt: str
    likelihood_tolerance: float = 1e-10
    allowed_use: tuple[str, ...] = _BENCHMARK_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _BENCHMARK_FORBIDDEN_USE
    universal_winner: None = None
    scalar_score: None = None

    def __post_init__(self) -> None:
        if not isinstance(self.mes_disposition, MesBenchmarkDisposition):
            raise AnchorGeometryError(
                "mes_disposition must be a MesBenchmarkDisposition"
            )
        object.__setattr__(
            self,
            "likelihood_tolerance",
            _nonnegative(
                self.likelihood_tolerance,
                "likelihood_tolerance",
            ),
        )
        _sha256_identity(self.base_draws_receipt, "base_draws_receipt")
        object.__setattr__(
            self, "allowed_use", _texts(self.allowed_use, "allowed_use")
        )
        object.__setattr__(
            self, "forbidden_use", _texts(self.forbidden_use, "forbidden_use")
        )
        if self.universal_winner is not None or self.scalar_score is not None:
            raise AnchorGeometryError(
                "normalizer benchmarks must not expose a universal winner or score"
            )
        _validate_normalizer_benchmark_report(self)

    def as_payload(self) -> dict[str, object]:
        return {
            "schema_version": "common.normalizer_benchmark.v1",
            "base_draws_receipt": self.base_draws_receipt,
            "likelihood_tolerance": self.likelihood_tolerance,
            "mes_disposition": self.mes_disposition.value,
            "pareto_fronts": {
                front.purpose.value: {
                    "normalizer_ids": list(front.normalizer_ids),
                    "metric_ids": list(front.metric_ids),
                }
                for front in self.pareto_fronts
            },
            "universal_winner": None,
            "scalar_score": None,
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def _dominates(
    left: NormalizerEvaluation,
    right: NormalizerEvaluation,
) -> bool:
    left_metrics = {metric.metric_id: metric for metric in left.metrics}
    right_metrics = {metric.metric_id: metric for metric in right.metrics}
    weak = []
    strict = []
    for metric_id in sorted(left_metrics):
        left_metric = left_metrics[metric_id]
        right_metric = right_metrics[metric_id]
        if left_metric.direction is MetricDirection.LOWER_IS_BETTER:
            weak.append(left_metric.value <= right_metric.value)
            strict.append(left_metric.value < right_metric.value)
        else:
            weak.append(left_metric.value >= right_metric.value)
            strict.append(left_metric.value > right_metric.value)
    return all(weak) and any(strict)


def _validate_normalizer_benchmark_report(
    report: NormalizerBenchmarkReport,
) -> None:
    """Make direct construction obey the same benchmark contract as the builder."""

    specs = tuple(report.specs)
    evaluations = tuple(report.evaluations)
    fronts = tuple(report.pareto_fronts)
    if not specs or not evaluations or not fronts:
        raise AnchorGeometryError(
            "benchmark specs, evaluations, and Pareto fronts must not be empty"
        )
    if any(not isinstance(spec, NormalizerSpec) for spec in specs):
        raise AnchorGeometryError(
            "specs must contain NormalizerSpec values"
        )
    if any(
        not isinstance(evaluation, NormalizerEvaluation)
        for evaluation in evaluations
    ):
        raise AnchorGeometryError(
            "evaluations must contain NormalizerEvaluation values"
        )
    if any(not isinstance(front, PurposeParetoFront) for front in fronts):
        raise AnchorGeometryError(
            "pareto_fronts must contain PurposeParetoFront values"
        )
    object.__setattr__(report, "specs", specs)
    object.__setattr__(report, "evaluations", evaluations)
    object.__setattr__(report, "pareto_fronts", fronts)

    spec_by_id = {spec.normalizer_id: spec for spec in specs}
    if len(spec_by_id) != len(specs):
        raise AnchorGeometryError("normalizer_id values must be unique")
    kinds = tuple(spec.kind for spec in specs)
    if set(kinds) != set(NormalizerKind) or len(kinds) != len(NormalizerKind):
        raise AnchorGeometryError(
            "the benchmark requires exactly one spec for every normalizer kind"
        )
    if len({spec.coordinate_labels for spec in specs}) != 1:
        raise AnchorGeometryError(
            "all normalizers must act on the same coordinate channel"
        )
    if {
        frozenset(spec.purposes) for spec in specs
    } != {frozenset(NormalizerPurpose)}:
        raise AnchorGeometryError(
            "every normalizer must declare the complete shared purpose set"
        )

    receipts = {
        evaluation.base_draws_receipt for evaluation in evaluations
    }
    if receipts != {report.base_draws_receipt}:
        raise AnchorGeometryError(
            "all normalizer evaluations and the report must use the same base draws"
        )
    expected_pairs = {
        (spec.normalizer_id, purpose)
        for spec in specs
        for purpose in spec.purposes
    }
    actual_pairs = {
        (evaluation.normalizer_id, evaluation.purpose)
        for evaluation in evaluations
    }
    if len(actual_pairs) != len(evaluations):
        raise AnchorGeometryError(
            "normalizer/purpose evaluations must be unique"
        )
    if actual_pairs != expected_pairs:
        raise AnchorGeometryError(
            "evaluations must cover every declared normalizer/purpose pair"
        )
    for evaluation in evaluations:
        spec = spec_by_id[evaluation.normalizer_id]
        if (
            spec.availability is NormalizerAvailability.AVAILABLE
            and evaluation.status is not NormalizerEvaluationStatus.EVALUATED
        ) or (
            spec.availability is NormalizerAvailability.UNAVAILABLE
            and evaluation.status is not NormalizerEvaluationStatus.UNAVAILABLE
        ):
            raise AnchorGeometryError(
                "normalizer availability and evaluation status disagree"
            )
        if (
            evaluation.status is NormalizerEvaluationStatus.EVALUATED
            and evaluation.likelihood_invariance_error
            > report.likelihood_tolerance
        ):
            raise AnchorGeometryError(
                "exact transformed-likelihood invariance exceeded tolerance"
            )
        if (
            evaluation.denominator_zero_status
            is not DenominatorZeroStatus.FAIL_CLOSED
        ):
            raise AnchorGeometryError(
                "normalizer benchmark denominator-zero probes must fail closed"
            )

    front_by_purpose = {front.purpose: front for front in fronts}
    if len(front_by_purpose) != len(fronts):
        raise AnchorGeometryError(
            "Pareto fronts must be unique by purpose"
        )
    if set(front_by_purpose) != set(NormalizerPurpose):
        raise AnchorGeometryError(
            "Pareto fronts must cover every registered normalizer purpose"
        )
    for purpose in NormalizerPurpose:
        active = tuple(
            evaluation
            for evaluation in evaluations
            if evaluation.purpose is purpose
            and evaluation.status is NormalizerEvaluationStatus.EVALUATED
        )
        if not active:
            raise AnchorGeometryError(
                f"purpose {purpose.value} has no available evaluation"
            )
        signatures = {
            tuple(
                sorted(
                    (metric.metric_id, metric.direction.value)
                    for metric in evaluation.metrics
                )
            )
            for evaluation in active
        }
        if len(signatures) != 1:
            raise AnchorGeometryError(
                "all evaluations within a purpose need identical metric semantics"
            )
        expected_ids = tuple(
            sorted(
                evaluation.normalizer_id
                for evaluation in active
                if not any(
                    other is not evaluation
                    and _dominates(other, evaluation)
                    for other in active
                )
            )
        )
        expected_metric_ids = tuple(
            metric_id for metric_id, _ in next(iter(signatures))
        )
        front = front_by_purpose[purpose]
        if (
            front.normalizer_ids != expected_ids
            or front.metric_ids != expected_metric_ids
        ):
            raise AnchorGeometryError(
                "Pareto front must be derived exactly from its evaluations"
            )

    mes_spec = next(
        spec for spec in specs if spec.kind is NormalizerKind.MES_ANCHORED
    )
    if mes_spec.availability is NormalizerAvailability.UNAVAILABLE:
        expected_disposition = MesBenchmarkDisposition.UNAVAILABLE
    elif all(
        front_by_purpose[purpose].normalizer_ids
        == (mes_spec.normalizer_id,)
        for purpose in mes_spec.purposes
    ):
        expected_disposition = (
            MesBenchmarkDisposition.PRIMARY_FOR_REGISTERED_PURPOSES
        )
    else:
        expected_disposition = MesBenchmarkDisposition.ONE_ANCHOR_AMONG_FAMILY
    if report.mes_disposition is not expected_disposition:
        raise AnchorGeometryError(
            "mes_disposition must be derived exactly from the Pareto fronts"
        )


def build_normalizer_benchmark(
    *,
    specs: Sequence[NormalizerSpec],
    evaluations: Sequence[NormalizerEvaluation],
    likelihood_tolerance: float = 1e-10,
) -> NormalizerBenchmarkReport:
    """Build purpose-specific Pareto fronts from one registered draw set."""

    tolerance = _nonnegative(likelihood_tolerance, "likelihood_tolerance")
    specs_tuple = tuple(specs)
    evaluations_tuple = tuple(evaluations)
    if not specs_tuple or not evaluations_tuple:
        raise AnchorGeometryError("specs and evaluations must not be empty")
    if any(not isinstance(spec, NormalizerSpec) for spec in specs_tuple):
        raise AnchorGeometryError("specs must contain NormalizerSpec values")
    if any(
        not isinstance(evaluation, NormalizerEvaluation)
        for evaluation in evaluations_tuple
    ):
        raise AnchorGeometryError(
            "evaluations must contain NormalizerEvaluation values"
        )
    spec_by_id = {spec.normalizer_id: spec for spec in specs_tuple}
    if len(spec_by_id) != len(specs_tuple):
        raise AnchorGeometryError("normalizer_id values must be unique")
    kinds = tuple(spec.kind for spec in specs_tuple)
    if set(kinds) != set(NormalizerKind) or len(kinds) != len(NormalizerKind):
        raise AnchorGeometryError(
            "the benchmark requires exactly one spec for every normalizer kind"
        )
    coordinate_channels = {
        spec.coordinate_labels for spec in specs_tuple
    }
    if len(coordinate_channels) != 1:
        raise AnchorGeometryError(
            "all normalizers must act on the same coordinate channel"
        )
    purpose_sets = {frozenset(spec.purposes) for spec in specs_tuple}
    if purpose_sets != {frozenset(NormalizerPurpose)}:
        raise AnchorGeometryError(
            "every normalizer must declare the complete shared purpose set"
        )
    receipts = {evaluation.base_draws_receipt for evaluation in evaluations_tuple}
    if len(receipts) != 1:
        raise AnchorGeometryError(
            "all normalizer evaluations must use the same base draws"
        )
    base_draws_receipt = next(iter(receipts))

    expected_pairs = {
        (spec.normalizer_id, purpose)
        for spec in specs_tuple
        for purpose in spec.purposes
    }
    actual_pairs = {
        (evaluation.normalizer_id, evaluation.purpose)
        for evaluation in evaluations_tuple
    }
    if len(actual_pairs) != len(evaluations_tuple):
        raise AnchorGeometryError(
            "normalizer/purpose evaluations must be unique"
        )
    if actual_pairs != expected_pairs:
        raise AnchorGeometryError(
            "evaluations must cover every declared normalizer/purpose pair"
        )
    for evaluation in evaluations_tuple:
        spec = spec_by_id[evaluation.normalizer_id]
        if (
            spec.availability is NormalizerAvailability.AVAILABLE
            and evaluation.status is not NormalizerEvaluationStatus.EVALUATED
        ) or (
            spec.availability is NormalizerAvailability.UNAVAILABLE
            and evaluation.status is not NormalizerEvaluationStatus.UNAVAILABLE
        ):
            raise AnchorGeometryError(
                "normalizer availability and evaluation status disagree"
            )
        if (
            evaluation.status is NormalizerEvaluationStatus.EVALUATED
            and evaluation.likelihood_invariance_error > tolerance
        ):
            raise AnchorGeometryError(
                "exact transformed-likelihood invariance exceeded tolerance"
            )
        if (
            evaluation.denominator_zero_status
            is not DenominatorZeroStatus.FAIL_CLOSED
        ):
            raise AnchorGeometryError(
                "normalizer benchmark denominator-zero probes must fail closed"
            )

    fronts: list[PurposeParetoFront] = []
    purposes = sorted(
        {purpose for spec in specs_tuple for purpose in spec.purposes},
        key=lambda item: item.value,
    )
    for purpose in purposes:
        active = tuple(
            evaluation
            for evaluation in evaluations_tuple
            if evaluation.purpose is purpose
            and evaluation.status is NormalizerEvaluationStatus.EVALUATED
        )
        if not active:
            raise AnchorGeometryError(
                f"purpose {purpose.value} has no available evaluation"
            )
        signatures = {
            tuple(
                sorted(
                    (metric.metric_id, metric.direction.value)
                    for metric in evaluation.metrics
                )
            )
            for evaluation in active
        }
        if len(signatures) != 1:
            raise AnchorGeometryError(
                "all evaluations within a purpose need identical metric semantics"
            )
        front = tuple(
            evaluation.normalizer_id
            for evaluation in active
            if not any(
                other is not evaluation and _dominates(other, evaluation)
                for other in active
            )
        )
        metric_ids = tuple(
            metric_id for metric_id, _ in next(iter(signatures))
        )
        fronts.append(
            PurposeParetoFront(
                purpose=purpose,
                normalizer_ids=tuple(sorted(front)),
                metric_ids=metric_ids,
            )
        )

    mes_spec = next(spec for spec in specs_tuple if spec.kind is NormalizerKind.MES_ANCHORED)
    if mes_spec.availability is NormalizerAvailability.UNAVAILABLE:
        mes_disposition = MesBenchmarkDisposition.UNAVAILABLE
    elif all(
        front.normalizer_ids == (mes_spec.normalizer_id,)
        for front in fronts
        if front.purpose in mes_spec.purposes
    ):
        mes_disposition = MesBenchmarkDisposition.PRIMARY_FOR_REGISTERED_PURPOSES
    else:
        mes_disposition = MesBenchmarkDisposition.ONE_ANCHOR_AMONG_FAMILY
    return NormalizerBenchmarkReport(
        specs=specs_tuple,
        evaluations=evaluations_tuple,
        pareto_fronts=tuple(fronts),
        mes_disposition=mes_disposition,
        base_draws_receipt=base_draws_receipt,
        likelihood_tolerance=tolerance,
    )


@dataclass(frozen=True)
class AnchorScalingInvarianceReport:
    original_rank: int
    transformed_rank: int
    original_quadratic: float
    transformed_quadratic: float
    absolute_error: float
    status: ScalingInvarianceStatus
    allowed_use: tuple[str, ...] = (
        "invertible-reparameterization consistency check",
    )
    forbidden_use: tuple[str, ...] = (
        "information gain from scaling",
        "rank gain from scaling",
    )


def check_anchor_scaling_invariance(
    *,
    state: object,
    response: object,
    anchor_scaling: object,
    observed: object,
    covariance: object,
    atol: float = 1e-10,
) -> AnchorScalingInvarianceReport:
    """Check ``R u == (R D)(D^-1 u)`` in one Gaussian response likelihood."""

    state_array = _array(state, "state", ndim=1)
    dimension = state_array.size
    response_array = _array(response, "response", ndim=2)
    if response_array.shape[1] != dimension:
        raise AnchorGeometryError(
            "response column count must match the state dimension"
        )
    observed_array = _array(
        observed, "observed", ndim=1, shape=(response_array.shape[0],)
    )
    scaling = _array(
        anchor_scaling,
        "anchor_scaling",
        ndim=2,
        shape=(dimension, dimension),
    )
    if int(np.linalg.matrix_rank(scaling)) != dimension:
        raise AnchorGeometryError("anchor_scaling must be invertible")
    covariance_array = _array(
        covariance,
        "covariance",
        ndim=2,
        shape=(response_array.shape[0], response_array.shape[0]),
    )
    if not np.allclose(
        covariance_array, covariance_array.T, rtol=0.0, atol=1e-12
    ):
        raise AnchorGeometryError("covariance must be symmetric")
    if float(np.min(np.linalg.eigvalsh(covariance_array))) <= 0.0:
        raise AnchorGeometryError("covariance must be positive definite")
    tolerance = _nonnegative(atol, "atol")

    transformed_state = np.linalg.solve(scaling, state_array)
    transformed_response = response_array @ scaling
    original_residual = observed_array - response_array @ state_array
    transformed_residual = (
        observed_array - transformed_response @ transformed_state
    )
    original_quadratic = float(
        original_residual
        @ np.linalg.solve(covariance_array, original_residual)
    )
    transformed_quadratic = float(
        transformed_residual
        @ np.linalg.solve(covariance_array, transformed_residual)
    )
    original_rank = int(np.linalg.matrix_rank(response_array))
    transformed_rank = int(np.linalg.matrix_rank(transformed_response))
    error = abs(original_quadratic - transformed_quadratic)
    status = (
        ScalingInvarianceStatus.PASS
        if original_rank == transformed_rank and error <= tolerance
        else ScalingInvarianceStatus.FAIL
    )
    return AnchorScalingInvarianceReport(
        original_rank=original_rank,
        transformed_rank=transformed_rank,
        original_quadratic=original_quadratic,
        transformed_quadratic=transformed_quadratic,
        absolute_error=error,
        status=status,
    )


@dataclass(frozen=True)
class ConjectureCounterexampleReport:
    claim_id: str
    counterexample_id: str
    scope: str
    exact_facts: tuple[tuple[str, str], ...]
    gate_outcome: str
    disposition: ConjectureDisposition
    allowed_use: tuple[str, ...]
    forbidden_use: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "counterexample_id": self.counterexample_id,
            "scope": self.scope,
            "exact_facts": dict(self.exact_facts),
            "gate_outcome": self.gate_outcome,
            "disposition": self.disposition.value,
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def j1_outer_envelope_counterexample() -> ConjectureCounterexampleReport:
    """Containment alone entails neither equality nor anchor uniqueness."""

    return ConjectureCounterexampleReport(
        claim_id="J1-EXACT",
        counterexample_id="J1-OUTER-ENVELOPE-NONUNIQUENESS-V1",
        scope="outer-envelope implication without an independent physical equality axiom",
        exact_facts=(
            ("physical_set", "[-1/2,1/2]"),
            ("anchor_a", "[-1,1]"),
            ("anchor_b", "[-2,2]"),
            ("rho_a_at_1_over_2", "1/2"),
            ("rho_b_at_1_over_2", "1/4"),
            ("containment", "H_subset_A_and_H_subset_B"),
            ("conclusion", "containment_does_not_imply_equality_or_uniqueness"),
        ),
        gate_outcome="COUNTEREXAMPLE_FOUND",
        disposition=ConjectureDisposition.REFUTED_OR_RESTRICTED,
        allowed_use=("restrict the general J1-EXACT conjecture",),
        forbidden_use=(
            "claim that no narrower physical MES uniqueness theorem is possible",
            "FLRW proximity or detection",
        ),
    )


def j2_dependence_counterexample() -> ConjectureCounterexampleReport:
    """Equal marginals can produce different raw-ratio exceedance laws."""

    return ConjectureCounterexampleReport(
        claim_id="J2-UNIFORM",
        counterexample_id="J2-JOINT-DEPENDENCE-V1",
        scope="joint-law-free or marginal-only calibration over a composite null",
        exact_facts=(
            ("numerator_marginal", "P(1)=1/2,P(2)=1/2"),
            ("anchor_marginal", "P(1)=1/2,P(2)=1/2"),
            ("comonotone_joint", "(1,1),(2,2) each probability 1/2"),
            ("comonotone_exceedance_probability", "0"),
            ("countermonotone_joint", "(1,2),(2,1) each probability 1/2"),
            ("countermonotone_exceedance_probability", "1/2"),
            (
                "conclusion",
                "equal_marginals_do_not_determine_raw_ratio_exceedance",
            ),
        ),
        gate_outcome="COUNTEREXAMPLE_FOUND",
        disposition=ConjectureDisposition.REFUTED_OR_RESTRICTED,
        allowed_use=(
            "require a registered joint numerator-anchor law",
            "restrict the general J2-UNIFORM conjecture",
        ),
        forbidden_use=(
            "claim that every registered joint-law test is invalid",
            "serialize raw excess as calibrated evidence",
        ),
    )


__all__ = [
    "AdditiveRadialMargin",
    "AnchorAvailability",
    "AnchorBlockSpec",
    "AnchorBodySpec",
    "AnchorFamily",
    "AnchorFamilyKind",
    "AnchorGaugeInterval",
    "AnchorGaugeStatus",
    "AnchorGeometryError",
    "AnchorGeometryKind",
    "AnchorMarginReport",
    "AnchorMarginStatus",
    "AnchorScalingInvarianceReport",
    "AnchorVector",
    "BenchmarkMetric",
    "ConjectureCounterexampleReport",
    "ConjectureDisposition",
    "DenominatorZeroStatus",
    "MarginIntervalStatus",
    "MesBenchmarkDisposition",
    "MetricDirection",
    "MultiplicativeBoundaryScale",
    "NormalizerAvailability",
    "NormalizerBenchmarkReport",
    "NormalizerEvaluation",
    "NormalizerEvaluationStatus",
    "NormalizerKind",
    "NormalizerPurpose",
    "NormalizerSpec",
    "PolytopeHalfspace",
    "PurposeParetoFront",
    "RawAnchorExcess",
    "RelativeBoundaryGrowth",
    "ScalingInvarianceStatus",
    "build_anchor_margin_report",
    "build_normalizer_benchmark",
    "check_anchor_scaling_invariance",
    "evaluate_anchor_gauge",
    "j1_outer_envelope_counterexample",
    "j2_dependence_counterexample",
]

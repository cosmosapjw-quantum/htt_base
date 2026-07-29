"""Supported-quotient anchored response and nonlinearity diagnostics.

The response layer in this module is deliberately matrix valued.  It keeps
four operations separate:

* an invertible premise-anchor coordinate map;
* whitening on the positive-eigenvalue support of one declared covariance;
* nuisance-tangent projection in that supported data space; and
* held-out nonlinear attribution already validated by
  :mod:`common.orbit_nonlinearity`.

Missing responses are never replaced by zero columns.  Components in the
covariance null space are returned explicitly, and a rank gain is never
collapsed to a finite volume-contraction scalar.  These are pre-solver,
diagnostic-only contracts; they are not evidence for FLRW departure, geometry
detection, a native solver, or Bianchi family identification.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Real
from typing import Sequence

import numpy as np

from common.anchor_geometry import (
    AnchorGaugeInterval,
    AnchorGaugeStatus,
    NormalizerAvailability,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.orbit_nonlinearity import (
    CandidateKind,
    NonlinearityAttributionStatus,
    NonlinearityReport,
    revalidate_nonlinearity_report,
)
from common.transfer_registry import TransferFunctionSpec, TransferSource


class AnchoredResponseGeometryError(ValueError):
    """Raised when a response-geometry contract is incomplete or inconsistent."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class AnchoredResponseStatus(_StringEnum):
    MEASURED = "MEASURED"
    EXPLICIT_NULL_RESPONSE = "EXPLICIT_NULL_RESPONSE"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"
    MISSING_INPUT = "MISSING_INPUT"


class PrincipalAngleStatus(_StringEnum):
    DEFINED = "DEFINED"
    EMPTY_SUBSPACE = "EMPTY_SUBSPACE"
    NOT_REQUESTED = "NOT_REQUESTED"


class IdentifiedSetContractionStatus(_StringEnum):
    DEFINED_FULL_DIMENSION = "DEFINED_FULL_DIMENSION"
    DEFINED_COMMON_SUPPORTED_SUBSPACE = "DEFINED_COMMON_SUPPORTED_SUBSPACE"
    RANK_GAIN_NO_FINITE_RATIO = "RANK_GAIN_NO_FINITE_RATIO"
    SUBSPACE_CHANGED = "SUBSPACE_CHANGED"
    NO_IDENTIFIED_SUBSPACE = "NO_IDENTIFIED_SUBSPACE"


class SchurMorphologyStatus(_StringEnum):
    MEASURED = "MEASURED"
    EXPLICIT_NULL_RESPONSE = "EXPLICIT_NULL_RESPONSE"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"
    MISSING_INPUT = "MISSING_INPUT"


class NonlinearityDGPKind(_StringEnum):
    LINEAR_ANCHOR_COMPATIBLE = "LINEAR_ANCHOR_COMPATIBLE"
    LINEAR_PREMISE_MISMATCH = "LINEAR_PREMISE_MISMATCH"
    NONLINEAR_ANCHOR_COMPATIBLE = "NONLINEAR_ANCHOR_COMPATIBLE"
    NONLINEAR_PLUS_EXCEEDANCE = "NONLINEAR_PLUS_EXCEEDANCE"
    OBSERVER_FRAME_MISMATCH = "OBSERVER_FRAME_MISMATCH"
    DERIVATIVE_CONTROL_FAILURE = "DERIVATIVE_CONTROL_FAILURE"
    SYSTEMATICS_MIMIC = "SYSTEMATICS_MIMIC"
    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"


class NonlinearityPhaseStatus(_StringEnum):
    LINEAR_PREMISE_COMPATIBLE = "LINEAR_PREMISE_COMPATIBLE"
    LINEAR_PREMISE_MISMATCH = "LINEAR_PREMISE_MISMATCH"
    NONLINEAR_WITHIN_ANCHOR = "NONLINEAR_WITHIN_ANCHOR"
    NONLINEAR_AND_EXCEEDANCE = "NONLINEAR_AND_EXCEEDANCE"
    ANCHOR_INTERVAL_STRADDLES_BOUNDARY = "ANCHOR_INTERVAL_STRADDLES_BOUNDARY"
    UNATTRIBUTED_OFF_MANIFOLD = "UNATTRIBUTED_OFF_MANIFOLD"
    NON_IDENTIFIED_RESPONSE = "NON_IDENTIFIED_RESPONSE"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"
    MISSING_RESPONSE = "MISSING_RESPONSE"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"


_ALLOWED_USE = (
    "pre-solver supported-quotient response diagnostic",
    "matrix-valued conditional morphology information",
    "synthetic held-out source-competition methodology",
)
_FORBIDDEN_USE = (
    "FLRW departure or geometry detection",
    "Bianchi family identification",
    "native solver validation",
    "posterior, Bayes factor, e-value, or evidence from anchor scaling",
)
_GEOMETRY_TOKEN = object()
_SCHUR_TOKEN = object()
_PHASE_CELL_TOKEN = object()
_PHASE_DIAGRAM_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AnchoredResponseGeometryError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise AnchoredResponseGeometryError(f"{name} must be a sequence")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise AnchoredResponseGeometryError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise AnchoredResponseGeometryError(
            f"{name} must not contain duplicates"
        )
    return out


def _receipt(value: object, name: str) -> str:
    out = _text(value, name)
    digest = out[7:] if out.startswith("sha256:") else ""
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise AnchoredResponseGeometryError(
            f"{name} must be a lowercase sha256 receipt identity"
        )
    return out


def _transfer_source(value: object) -> TransferSource:
    try:
        return value if isinstance(value, TransferSource) else TransferSource(str(value))
    except ValueError as exc:
        raise AnchoredResponseGeometryError(
            "transfer_source must use the registered TransferSource vocabulary"
        ) from exc


def _canonical_transfer_spec(
    value: object,
) -> TransferFunctionSpec:
    if type(value) is not TransferFunctionSpec:
        raise AnchoredResponseGeometryError(
            "non-none transfer sources require an exact TransferFunctionSpec"
        )
    try:
        canonical = TransferFunctionSpec(
            transfer_id=value.transfer_id,
            source=value.source,
            family=value.family,
            valid_range=value.valid_range,
            observable_kind=value.observable_kind,
            normalization=value.normalization,
            calibration_status=value.calibration_status,
            caveats=value.caveats,
            source_ref=value.source_ref,
            version=value.version,
            passed_validation_gates=value.passed_validation_gates,
        )
    except AttributeError as exc:
        raise AnchoredResponseGeometryError(
            "transfer_spec is missing validated provenance fields"
        ) from exc
    if canonical != value:
        raise AnchoredResponseGeometryError(
            "transfer_spec fields do not match constructor invariants"
        )
    return canonical


def _transfer_binding(
    *,
    transfer_id: object,
    transfer_source: object,
    transfer_spec: TransferFunctionSpec | None,
) -> tuple[str, TransferSource, TransferFunctionSpec | None]:
    source = _transfer_source(transfer_source)
    if source is TransferSource.NONE:
        if transfer_spec is not None:
            raise AnchoredResponseGeometryError(
                "transfer_source=none must not carry TransferFunctionSpec"
            )
        return _receipt(transfer_id, "transfer_id"), source, None
    if transfer_spec is None:
        raise AnchoredResponseGeometryError(
            "non-none transfer sources require TransferFunctionSpec"
        )
    canonical = _canonical_transfer_spec(transfer_spec)
    transfer = _text(transfer_id, "transfer_id")
    if canonical.source is not source:
        raise AnchoredResponseGeometryError(
            "transfer_source must match transfer_spec.source"
        )
    if canonical.transfer_id != transfer:
        raise AnchoredResponseGeometryError(
            "transfer_id must match transfer_spec.transfer_id"
        )
    return transfer, source, canonical


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise AnchoredResponseGeometryError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise AnchoredResponseGeometryError(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise AnchoredResponseGeometryError(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise AnchoredResponseGeometryError(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise AnchoredResponseGeometryError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise AnchoredResponseGeometryError(f"{name} must be non-negative")
    return out


def _relative_tolerance(value: object) -> float:
    out = _nonnegative(value, "rtol")
    if out == 0.0 or out > 1.0e-3:
        raise AnchoredResponseGeometryError(
            "rtol must be positive and at most 1e-3"
        )
    return out


def _contains_invalid_scalar(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, (complex, np.complexfloating)):
        return True
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        return True
    if isinstance(value, np.ndarray):
        if value.dtype.kind in {"b", "c", "O", "S", "U"}:
            return True
        return False
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
        raise AnchoredResponseGeometryError(
            f"{name} must contain finite real numeric values, not "
            "bool/text/complex"
        )
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise AnchoredResponseGeometryError(f"{name} must be numeric") from exc
    if ndim is not None and out.ndim != ndim:
        raise AnchoredResponseGeometryError(f"{name} must have ndim={ndim}")
    if shape is not None and out.shape != shape:
        raise AnchoredResponseGeometryError(
            f"{name} must have shape {shape}, got {out.shape}"
        )
    if out.size == 0:
        raise AnchoredResponseGeometryError(f"{name} must not be empty")
    if not np.isfinite(out).all():
        raise AnchoredResponseGeometryError(f"{name} must be finite")
    return out


def _matrix_tuple(value: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(item) for item in row) for row in value)


def _vector_tuple(value: np.ndarray) -> tuple[float, ...]:
    return tuple(float(item) for item in value)


def _array_content_identity(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value, dtype="<f8")
    header = json.dumps(
        {
            "dtype": "<f8",
            "schema": "HTT_ANCHORED_NUMERIC_ARRAY_V1",
            "shape": list(array.shape),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(header)
    digest.update(b"\0")
    digest.update(array.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def anchored_numeric_content_id(value: object) -> str:
    """Return the canonical content identity for one accepted numeric array."""

    return _array_content_identity(
        _array(value, "anchored_numeric_content", ndim=None)
    )


def _normalizer_matrix(
    normalizer: NormalizerSpec,
    labels: tuple[str, ...],
) -> np.ndarray:
    if not isinstance(normalizer, NormalizerSpec):
        raise AnchoredResponseGeometryError(
            "normalizer must be a NormalizerSpec"
        )
    if normalizer.availability is not NormalizerAvailability.AVAILABLE:
        raise AnchoredResponseGeometryError(
            "normalizer must be available; missing/withheld normalizers "
            "cannot become zero scaling"
        )
    if NormalizerPurpose.RESPONSE_CONDITIONING not in normalizer.purposes:
        raise AnchoredResponseGeometryError(
            "normalizer must declare the RESPONSE_CONDITIONING purpose"
        )
    if normalizer.coordinate_labels != labels:
        raise AnchoredResponseGeometryError(
            "normalizer and response parameter labels must match exactly"
        )
    matrix = _array(
        normalizer.coordinate_map,
        "normalizer.coordinate_map",
        ndim=2,
        shape=(len(labels), len(labels)),
    )
    if int(np.linalg.matrix_rank(matrix)) != len(labels):
        raise AnchoredResponseGeometryError(
            "normalizer coordinate_map must be invertible"
        )
    return matrix


def _covariance_support(
    covariance: object,
    *,
    dimension: int,
    rtol: float,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    float,
    np.ndarray,
    np.ndarray,
]:
    """Return support operators in a channel-unit-congruence invariant basis."""

    matrix = _array(
        covariance,
        "covariance",
        ndim=2,
        shape=(dimension, dimension),
    )
    epsilon = np.finfo(float).eps
    diagonal = np.diag(matrix)
    if np.any(diagonal < 0.0):
        raise AnchoredResponseGeometryError(
            "covariance must be positive semidefinite"
        )
    standard_deviations = np.where(
        diagonal > 0.0,
        np.sqrt(diagonal),
        1.0,
    )
    pair_scale = (
        standard_deviations[:, None] * standard_deviations[None, :]
    )
    entry_scale = np.maximum(
        np.maximum(np.abs(matrix), np.abs(matrix.T)),
        pair_scale,
    )
    symmetry_tolerance = 64.0 * epsilon * entry_scale
    if np.any(np.abs(matrix - matrix.T) > symmetry_tolerance):
        raise AnchoredResponseGeometryError("covariance must be symmetric")
    zero_variance = diagonal == 0.0
    if np.any(matrix[zero_variance, :] != 0.0) or np.any(
        matrix[:, zero_variance] != 0.0
    ):
        raise AnchoredResponseGeometryError(
            "covariance must be positive semidefinite; a zero-variance "
            "channel cannot carry cross covariance"
        )
    inverse_scale = 1.0 / standard_deviations
    standardizer = np.diag(inverse_scale)
    # Support, PSD, and relative-rank decisions belong to the dimensionless
    # correlation geometry. A global covariance scale would make those
    # decisions depend on the arbitrary units of an unrelated channel.
    standardized = (
        inverse_scale[:, None] * matrix * inverse_scale[None, :]
    )
    standardized = 0.5 * (standardized + standardized.T)
    eigenvalues, eigenvectors = np.linalg.eigh(standardized)
    spectral_scale = float(np.max(np.abs(eigenvalues), initial=0.0))
    # PSD validity is a backward-error check, not the user-selected support
    # threshold. Reusing ``rtol`` here could accept a physically indefinite
    # covariance merely because another channel has a large variance.
    psd_tolerance = (
        256.0
        * epsilon
        * max(dimension, 1) ** 2
        * max(spectral_scale, 1.0)
    )
    if eigenvalues.size and float(np.min(eigenvalues)) < -psd_tolerance:
        raise AnchoredResponseGeometryError(
            "covariance must be positive semidefinite"
        )
    eigenvalues = np.maximum(eigenvalues, 0.0)
    tolerance = rtol * max(
        float(np.max(eigenvalues, initial=0.0)),
        1.0,
    )
    support = eigenvalues > tolerance
    support_vectors = eigenvectors[:, support]
    support_values = eigenvalues[support]
    supported_standardized = (
        standardized
        if np.all(support)
        else support_vectors
        @ np.diag(support_values)
        @ support_vectors.T
    )
    whitener = (
        (
            support_vectors.T
            * inverse_scale[None, :]
            / np.sqrt(support_values)[:, None]
        )
        if support_values.size
        else np.empty((0, dimension), dtype=float)
    )
    null_vectors = inverse_scale[:, None] * eigenvectors[:, ~support]
    return (
        matrix,
        whitener,
        null_vectors,
        tolerance,
        standardizer,
        supported_standardized,
    )


def _project_nuisance(
    supported_response: np.ndarray,
    supported_nuisance: np.ndarray | None,
    *,
    rtol: float,
) -> tuple[np.ndarray, int, np.ndarray]:
    supported_dimension = supported_response.shape[0]
    if supported_nuisance is None:
        projector = np.eye(supported_dimension)
        return supported_response, 0, projector
    if supported_nuisance.shape[0] != supported_dimension:
        raise AnchoredResponseGeometryError(
            "supported nuisance and response row counts must agree"
        )
    if supported_dimension == 0:
        return supported_response, 0, np.empty((0, 0), dtype=float)
    u, singular, _ = np.linalg.svd(
        supported_nuisance, full_matrices=False
    )
    scale = float(singular[0]) if singular.size else 0.0
    rank = int(np.count_nonzero(singular > rtol * scale))
    basis = u[:, :rank]
    projector = np.eye(supported_dimension) - basis @ basis.T
    return projector @ supported_response, rank, projector


def _svd(
    matrix: np.ndarray,
    *,
    rtol: float,
) -> tuple[int, np.ndarray, np.ndarray, float]:
    if matrix.shape[0] == 0:
        return (
            0,
            np.empty((0,), dtype=float),
            np.eye(matrix.shape[1], dtype=float),
            0.0,
        )
    _, singular, vt = np.linalg.svd(matrix, full_matrices=True)
    scale = float(singular[0]) if singular.size else 0.0
    tolerance = rtol * scale
    rank = int(np.count_nonzero(singular > tolerance))
    return rank, singular, vt, tolerance


def _principal_angles(
    left: np.ndarray,
    right: np.ndarray,
    *,
    rtol: float,
) -> tuple[int, int, tuple[float, ...], PrincipalAngleStatus]:
    left_rank, left_singular, _, _ = _svd(left, rtol=rtol)
    right_rank, right_singular, _, _ = _svd(right, rtol=rtol)
    if left_rank == 0 or right_rank == 0:
        return left_rank, right_rank, (), PrincipalAngleStatus.EMPTY_SUBSPACE
    left_u = np.linalg.svd(left, full_matrices=False)[0][:, :left_rank]
    right_u = np.linalg.svd(right, full_matrices=False)[0][:, :right_rank]
    del left_singular, right_singular
    cosines = np.linalg.svd(left_u.T @ right_u, compute_uv=False)
    angles = np.arccos(np.clip(cosines, -1.0, 1.0))
    return (
        left_rank,
        right_rank,
        tuple(float(value) for value in angles),
        PrincipalAngleStatus.DEFINED,
    )


@dataclass(frozen=True)
class PrincipalAngleReport:
    status: PrincipalAngleStatus
    left_rank: int | None
    right_rank: int | None
    angles_radians: tuple[float, ...]
    comparison_response_id: str | None

    def as_payload(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "left_rank": self.left_rank,
            "right_rank": self.right_rank,
            "angles_radians": list(self.angles_radians),
            "comparison_response_id": self.comparison_response_id,
        }


@dataclass(frozen=True)
class AnchoredResponseGeometryReport:
    status: AnchoredResponseStatus
    rank: int | None
    original_rank: int | None
    parameter_dimension: int | None
    data_dimension: int | None
    supported_data_dimension: int | None
    nuisance_rank: int | None
    singular_values: tuple[float, ...]
    reachable_directions: tuple[tuple[float, ...], ...]
    null_directions: tuple[tuple[float, ...], ...]
    covariance_null_response: tuple[tuple[float, ...], ...]
    covariance_null_response_norm_sq: float | None
    tolerance: float | None
    relative_tolerance: float | None
    parameter_labels: tuple[str, ...]
    normalizer_id: str | None
    normalizer_source_identity: str | None
    transfer_id: str | None
    transfer_source: TransferSource | None
    transfer_spec: TransferFunctionSpec | None
    mask_id: str | None
    covariance_id: str | None
    response_id: str | None
    covariance_content_id: str | None
    nuisance_response_id: str | None
    response_replay_matrix: tuple[tuple[float, ...], ...] | None
    covariance_replay_matrix: tuple[tuple[float, ...], ...] | None
    nuisance_replay_matrix: tuple[tuple[float, ...], ...] | None
    anchored_response_replay_matrix: tuple[tuple[float, ...], ...] | None
    principal_angles: PrincipalAngleReport
    missing_inputs: tuple[str, ...]
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _GEOMETRY_TOKEN:
            raise AnchoredResponseGeometryError(
                "AnchoredResponseGeometryReport must be created by "
                "measure_anchored_response_geometry"
            )
        if not isinstance(self.status, AnchoredResponseStatus):
            raise AnchoredResponseGeometryError(
                "status must be an AnchoredResponseStatus"
            )
        if not isinstance(self.principal_angles, PrincipalAngleReport):
            raise AnchoredResponseGeometryError(
                "principal_angles must be a PrincipalAngleReport"
            )
        if (
            self.transfer_source is not None
            and not isinstance(self.transfer_source, TransferSource)
        ):
            raise AnchoredResponseGeometryError(
                "transfer_source must be a TransferSource"
            )
        if self.transfer_source is TransferSource.NONE:
            if self.transfer_spec is not None:
                raise AnchoredResponseGeometryError(
                    "transfer_source=none must not carry TransferFunctionSpec"
                )
        elif self.transfer_source is not None:
            if self.transfer_spec is None:
                if not (
                    self.status is AnchoredResponseStatus.MISSING_INPUT
                    and "transfer_spec" in self.missing_inputs
                ):
                    raise AnchoredResponseGeometryError(
                        "non-none transfer sources require an exact "
                        "TransferFunctionSpec"
                    )
            else:
                canonical_spec = _canonical_transfer_spec(self.transfer_spec)
                if canonical_spec.source is not self.transfer_source:
                    raise AnchoredResponseGeometryError(
                        "transfer provenance fields must match"
                    )
                if (
                    canonical_spec.transfer_id != self.transfer_id
                    and not (
                        self.status is AnchoredResponseStatus.MISSING_INPUT
                        and self.transfer_id is None
                        and "transfer_id" in self.missing_inputs
                    )
                ):
                    raise AnchoredResponseGeometryError(
                        "transfer provenance fields must match"
                    )
        elif self.transfer_spec is not None:
            if not (
                self.status is AnchoredResponseStatus.MISSING_INPUT
                and "transfer_source" in self.missing_inputs
            ):
                raise AnchoredResponseGeometryError(
                    "transfer_spec requires transfer_source"
                )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise AnchoredResponseGeometryError(
                "response geometry must retain the registered claim boundary"
            )

    @property
    def identifiable(self) -> bool:
        return (
            self.rank is not None
            and self.parameter_dimension is not None
            and self.rank == self.parameter_dimension
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "rank": self.rank,
            "original_rank": self.original_rank,
            "parameter_dimension": self.parameter_dimension,
            "data_dimension": self.data_dimension,
            "supported_data_dimension": self.supported_data_dimension,
            "nuisance_rank": self.nuisance_rank,
            "singular_values": list(self.singular_values),
            "reachable_directions": [
                list(row) for row in self.reachable_directions
            ],
            "null_directions": [list(row) for row in self.null_directions],
            "covariance_null_response": [
                list(row) for row in self.covariance_null_response
            ],
            "covariance_null_response_norm_sq": (
                self.covariance_null_response_norm_sq
            ),
            "tolerance": self.tolerance,
            "relative_tolerance": self.relative_tolerance,
            "parameter_labels": list(self.parameter_labels),
            "normalizer_id": self.normalizer_id,
            "normalizer_source_identity": self.normalizer_source_identity,
            "transfer_id": self.transfer_id,
            "transfer_source": (
                None
                if self.transfer_source is None
                else self.transfer_source.value
            ),
            "transfer_metadata": (
                None
                if self.transfer_spec is None
                else self.transfer_spec.to_metadata()
            ),
            "mask_id": self.mask_id,
            "covariance_id": self.covariance_id,
            "response_id": self.response_id,
            "covariance_content_id": self.covariance_content_id,
            "nuisance_response_id": self.nuisance_response_id,
            "principal_angles": self.principal_angles.as_payload(),
            "missing_inputs": list(self.missing_inputs),
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def measure_anchored_response_geometry(
    *,
    response: object | None,
    covariance: object | None,
    normalizer: NormalizerSpec | None,
    parameter_labels: Sequence[object] | None,
    transfer_id: str | None,
    transfer_source: TransferSource | str | None,
    transfer_spec: TransferFunctionSpec | None = None,
    mask_id: str | None,
    covariance_id: str | None,
    nuisance_response: object | None = None,
    comparison_response: object | None = None,
    rtol: float = 1.0e-12,
) -> AnchoredResponseGeometryReport:
    """Measure ``P C_supp^-1/2 R D`` without inventing missing channels."""

    missing = tuple(
        name
        for name, value in (
            ("response", response),
            ("covariance", covariance),
            ("normalizer", normalizer),
            ("parameter_labels", parameter_labels),
            ("transfer_id", transfer_id),
            ("transfer_source", transfer_source),
            ("mask_id", mask_id),
            ("covariance_id", covariance_id),
        )
        if value is None
    )
    if (
        normalizer is not None
        and normalizer.availability is not NormalizerAvailability.AVAILABLE
    ):
        missing = tuple(dict.fromkeys((*missing, "normalizer_available")))
    normalized_source = (
        None
        if transfer_source is None
        else _transfer_source(transfer_source)
    )
    canonical_spec = (
        None
        if transfer_spec is None
        else _canonical_transfer_spec(transfer_spec)
    )
    if normalized_source is TransferSource.NONE and canonical_spec is not None:
        raise AnchoredResponseGeometryError(
            "transfer_source=none must not carry TransferFunctionSpec"
        )
    if (
        normalized_source is not None
        and normalized_source is not TransferSource.NONE
        and canonical_spec is None
    ):
        missing = tuple(dict.fromkeys((*missing, "transfer_spec")))
    if (
        canonical_spec is not None
        and normalized_source is not None
        and canonical_spec.source is not normalized_source
    ):
        raise AnchoredResponseGeometryError(
            "transfer_source must match transfer_spec.source"
        )
    if (
        canonical_spec is not None
        and transfer_id is not None
        and canonical_spec.transfer_id != transfer_id
    ):
        raise AnchoredResponseGeometryError(
            "transfer_id must match transfer_spec.transfer_id"
        )
    if missing:
        for name, value in (
            ("transfer_id", transfer_id),
            ("transfer_source", transfer_source),
            ("mask_id", mask_id),
            ("covariance_id", covariance_id),
        ):
            if value is not None:
                if name == "transfer_source":
                    _transfer_source(value)
                elif (
                    name == "transfer_id"
                    and (
                        (
                            normalized_source is not None
                            and normalized_source is not TransferSource.NONE
                        )
                        or canonical_spec is not None
                    )
                ):
                    _text(value, name)
                else:
                    _receipt(value, name)
        return AnchoredResponseGeometryReport(
            status=AnchoredResponseStatus.MISSING_INPUT,
            rank=None,
            original_rank=None,
            parameter_dimension=None,
            data_dimension=None,
            supported_data_dimension=None,
            nuisance_rank=None,
            singular_values=(),
            reachable_directions=(),
            null_directions=(),
            covariance_null_response=(),
            covariance_null_response_norm_sq=None,
            tolerance=None,
            relative_tolerance=None,
            parameter_labels=(),
            normalizer_id=(
                None if normalizer is None else normalizer.normalizer_id
            ),
            normalizer_source_identity=(
                None if normalizer is None else normalizer.source_identity
            ),
            transfer_id=transfer_id,
            transfer_source=(
                None
                if transfer_source is None
                else _transfer_source(transfer_source)
            ),
            transfer_spec=canonical_spec,
            mask_id=mask_id,
            covariance_id=covariance_id,
            response_id=None,
            covariance_content_id=None,
            nuisance_response_id=None,
            response_replay_matrix=None,
            covariance_replay_matrix=None,
            nuisance_replay_matrix=None,
            anchored_response_replay_matrix=None,
            principal_angles=PrincipalAngleReport(
                status=PrincipalAngleStatus.NOT_REQUESTED,
                left_rank=None,
                right_rank=None,
                angles_radians=(),
                comparison_response_id=None,
            ),
            missing_inputs=missing,
            _construction_token=_GEOMETRY_TOKEN,
        )

    tolerance = _relative_tolerance(rtol)
    labels = _texts(parameter_labels, "parameter_labels")
    matrix = _array(response, "response", ndim=2)
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise AnchoredResponseGeometryError(
            "response must have positive dimensions"
        )
    if matrix.shape[1] != len(labels):
        raise AnchoredResponseGeometryError(
            "response column count must match parameter_labels"
        )
    scaling = _normalizer_matrix(normalizer, labels)
    transfer, source, canonical_spec = _transfer_binding(
        transfer_id=transfer_id,
        transfer_source=transfer_source,
        transfer_spec=transfer_spec,
    )
    mask = _receipt(mask_id, "mask_id")
    covariance_receipt = _receipt(covariance_id, "covariance_id")
    (
        covariance_matrix,
        whitener,
        null_vectors,
        covariance_tolerance,
        covariance_standardizer,
        _,
    ) = _covariance_support(
        covariance,
        dimension=matrix.shape[0],
        rtol=tolerance,
    )
    covariance_content_id = _array_content_identity(covariance_matrix)
    if covariance_receipt != covariance_content_id:
        raise AnchoredResponseGeometryError(
            "covariance_id must match the canonical covariance content identity"
        )
    nuisance_matrix: np.ndarray | None = None
    supported_nuisance: np.ndarray | None = None
    if nuisance_response is not None:
        nuisance_matrix = _array(
            nuisance_response, "nuisance_response", ndim=2
        )
        if nuisance_matrix.shape[0] != matrix.shape[0]:
            raise AnchoredResponseGeometryError(
                "nuisance_response and response row counts must agree"
            )
        supported_nuisance = whitener @ nuisance_matrix
    supported = whitener @ matrix
    projected, nuisance_rank, projector = _project_nuisance(
        supported,
        supported_nuisance,
        rtol=tolerance,
    )
    anchored = projected @ scaling
    original_rank, _, _, _ = _svd(projected, rtol=tolerance)
    rank, singular, vt, rank_tolerance = _svd(
        anchored, rtol=tolerance
    )
    if rank != original_rank:
        raise AnchoredResponseGeometryError(
            "invertible anchor scaling changed the measured response rank"
        )
    covariance_null = null_vectors.T @ matrix @ scaling
    covariance_null_norm_sq = float(
        np.sum(covariance_null * covariance_null)
    )
    del covariance_tolerance
    scaled_response_norm_sq = float(
        np.sum((covariance_standardizer @ matrix @ scaling) ** 2)
    )
    null_threshold = tolerance * tolerance * scaled_response_norm_sq
    if whitener.shape[0] == 0:
        status = AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT
    elif covariance_null_norm_sq > null_threshold:
        status = AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE
    else:
        status = AnchoredResponseStatus.MEASURED

    if comparison_response is None:
        angle_report = PrincipalAngleReport(
            status=PrincipalAngleStatus.NOT_REQUESTED,
            left_rank=None,
            right_rank=None,
            angles_radians=(),
            comparison_response_id=None,
        )
    else:
        comparison = _array(
            comparison_response,
            "comparison_response",
            ndim=2,
            shape=matrix.shape,
        )
        comparison_supported = projector @ (whitener @ comparison) @ scaling
        left_rank, right_rank, angles, angle_status = _principal_angles(
            anchored,
            comparison_supported,
            rtol=tolerance,
        )
        angle_report = PrincipalAngleReport(
            status=angle_status,
            left_rank=left_rank,
            right_rank=right_rank,
            angles_radians=angles,
            comparison_response_id=_array_content_identity(comparison),
        )

    return AnchoredResponseGeometryReport(
        status=status,
        rank=rank,
        original_rank=original_rank,
        parameter_dimension=matrix.shape[1],
        data_dimension=matrix.shape[0],
        supported_data_dimension=whitener.shape[0],
        nuisance_rank=nuisance_rank,
        singular_values=tuple(float(value) for value in singular),
        reachable_directions=tuple(
            _vector_tuple(row) for row in vt[:rank]
        ),
        null_directions=tuple(_vector_tuple(row) for row in vt[rank:]),
        covariance_null_response=tuple(
            _vector_tuple(row) for row in covariance_null
        ),
        covariance_null_response_norm_sq=covariance_null_norm_sq,
        tolerance=rank_tolerance,
        relative_tolerance=tolerance,
        parameter_labels=labels,
        normalizer_id=normalizer.normalizer_id,
        normalizer_source_identity=normalizer.source_identity,
        transfer_id=transfer,
        transfer_source=source,
        transfer_spec=canonical_spec,
        mask_id=mask,
        covariance_id=covariance_receipt,
        response_id=_array_content_identity(matrix),
        covariance_content_id=covariance_content_id,
        nuisance_response_id=(
            None
            if nuisance_matrix is None
            else _array_content_identity(nuisance_matrix)
        ),
        response_replay_matrix=_matrix_tuple(matrix),
        covariance_replay_matrix=_matrix_tuple(covariance_matrix),
        nuisance_replay_matrix=(
            None
            if nuisance_matrix is None
            else _matrix_tuple(nuisance_matrix)
        ),
        anchored_response_replay_matrix=_matrix_tuple(anchored),
        principal_angles=angle_report,
        missing_inputs=(),
        _construction_token=_GEOMETRY_TOKEN,
    )


def revalidate_anchored_response_geometry(
    report: AnchoredResponseGeometryReport,
    *,
    normalizer: NormalizerSpec,
    comparison_response: object | None = None,
) -> AnchoredResponseGeometryReport:
    """Recompute a measured report from its replay inputs and exact identities."""

    if type(report) is not AnchoredResponseGeometryReport:
        raise AnchoredResponseGeometryError(
            "report must be an exact factory-derived "
            "AnchoredResponseGeometryReport"
        )
    if report.status is AnchoredResponseStatus.MISSING_INPUT:
        return report
    rebuilt = measure_anchored_response_geometry(
        response=report.response_replay_matrix,
        covariance=report.covariance_replay_matrix,
        normalizer=normalizer,
        parameter_labels=report.parameter_labels,
        transfer_id=report.transfer_id,
        transfer_source=report.transfer_source,
        transfer_spec=report.transfer_spec,
        mask_id=report.mask_id,
        covariance_id=report.covariance_id,
        nuisance_response=report.nuisance_replay_matrix,
        comparison_response=comparison_response,
        rtol=report.relative_tolerance,
    )
    if rebuilt != report:
        raise AnchoredResponseGeometryError(
            "report fields do not match replayed response geometry"
        )
    return rebuilt


def _fisher_rank(
    fisher: np.ndarray,
    *,
    rtol: float,
) -> tuple[int, np.ndarray, np.ndarray, float]:
    symmetric = 0.5 * (fisher + fisher.T)
    values, vectors = np.linalg.eigh(symmetric)
    scale = float(np.max(np.abs(values), initial=0.0))
    tolerance = rtol * scale
    if values.size and float(np.min(values)) < -tolerance:
        raise AnchoredResponseGeometryError(
            "information matrix must be positive semidefinite"
        )
    support = values > tolerance
    return (
        int(np.count_nonzero(support)),
        values[support],
        vectors[:, support],
        tolerance,
    )


@dataclass(frozen=True)
class IdentifiedSetContractionReport:
    status: IdentifiedSetContractionStatus
    baseline_rank: int
    joint_rank: int
    parameter_dimension: int
    log_pseudodeterminant_gain: float | None
    confidence_ellipsoid_volume_ratio: float | None
    common_subspace_tolerance: float
    contraction_kind: str = "LOCAL_GAUSSIAN_SUPPORTED_ELLIPSOID"
    global_feasible_set_status: str = "NOT_COMPUTED_NO_FEASIBLE_SET_INPUT"
    global_feasible_set_contraction: None = None

    def as_payload(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "baseline_rank": self.baseline_rank,
            "joint_rank": self.joint_rank,
            "parameter_dimension": self.parameter_dimension,
            "log_pseudodeterminant_gain": self.log_pseudodeterminant_gain,
            "confidence_ellipsoid_volume_ratio": (
                self.confidence_ellipsoid_volume_ratio
            ),
            "common_subspace_tolerance": self.common_subspace_tolerance,
            "contraction_kind": self.contraction_kind,
            "global_feasible_set_status": self.global_feasible_set_status,
            "global_feasible_set_contraction": (
                self.global_feasible_set_contraction
            ),
        }


def _identified_set_contraction(
    baseline_fisher: np.ndarray,
    joint_fisher: np.ndarray,
    *,
    rtol: float,
) -> IdentifiedSetContractionReport:
    baseline_rank, baseline_values, baseline_vectors, baseline_tolerance = (
        _fisher_rank(baseline_fisher, rtol=rtol)
    )
    joint_rank, joint_values, joint_vectors, joint_tolerance = _fisher_rank(
        joint_fisher, rtol=rtol
    )
    dimension = baseline_fisher.shape[0]
    del baseline_tolerance, joint_tolerance
    subspace_tolerance = max(
        100.0 * rtol,
        64.0 * np.finfo(float).eps * max(dimension, 1),
    )
    if joint_rank < baseline_rank:
        raise AnchoredResponseGeometryError(
            "adding a positive semidefinite information block reduced rank"
        )
    if joint_rank > baseline_rank:
        return IdentifiedSetContractionReport(
            status=IdentifiedSetContractionStatus.RANK_GAIN_NO_FINITE_RATIO,
            baseline_rank=baseline_rank,
            joint_rank=joint_rank,
            parameter_dimension=dimension,
            log_pseudodeterminant_gain=None,
            confidence_ellipsoid_volume_ratio=None,
            common_subspace_tolerance=subspace_tolerance,
        )
    if baseline_rank == 0:
        return IdentifiedSetContractionReport(
            status=IdentifiedSetContractionStatus.NO_IDENTIFIED_SUBSPACE,
            baseline_rank=0,
            joint_rank=0,
            parameter_dimension=dimension,
            log_pseudodeterminant_gain=None,
            confidence_ellipsoid_volume_ratio=None,
            common_subspace_tolerance=subspace_tolerance,
        )
    baseline_projector = baseline_vectors @ baseline_vectors.T
    joint_projector = joint_vectors @ joint_vectors.T
    if not np.allclose(
        baseline_projector,
        joint_projector,
        rtol=0.0,
        atol=subspace_tolerance,
    ):
        return IdentifiedSetContractionReport(
            status=IdentifiedSetContractionStatus.SUBSPACE_CHANGED,
            baseline_rank=baseline_rank,
            joint_rank=joint_rank,
            parameter_dimension=dimension,
            log_pseudodeterminant_gain=None,
            confidence_ellipsoid_volume_ratio=None,
            common_subspace_tolerance=subspace_tolerance,
        )
    log_gain = float(
        np.sum(np.log(joint_values)) - np.sum(np.log(baseline_values))
    )
    if log_gain < -subspace_tolerance:
        raise AnchoredResponseGeometryError(
            "joint information decreased on the common identified subspace"
        )
    log_gain = max(log_gain, 0.0)
    return IdentifiedSetContractionReport(
        status=(
            IdentifiedSetContractionStatus.DEFINED_FULL_DIMENSION
            if baseline_rank == dimension
            else IdentifiedSetContractionStatus.DEFINED_COMMON_SUPPORTED_SUBSPACE
        ),
        baseline_rank=baseline_rank,
        joint_rank=joint_rank,
        parameter_dimension=dimension,
        log_pseudodeterminant_gain=log_gain,
        confidence_ellipsoid_volume_ratio=math.exp(-0.5 * log_gain),
        common_subspace_tolerance=subspace_tolerance,
    )


@dataclass(frozen=True)
class SchurMorphologyInformationReport:
    status: SchurMorphologyStatus
    baseline_geometry: AnchoredResponseGeometryReport | None
    conditional_morphology_geometry: AnchoredResponseGeometryReport | None
    baseline_information: tuple[tuple[float, ...], ...]
    incremental_information: tuple[tuple[float, ...], ...]
    joint_information: tuple[tuple[float, ...], ...]
    conditional_response: tuple[tuple[float, ...], ...]
    conditional_covariance: tuple[tuple[float, ...], ...]
    contraction: IdentifiedSetContractionReport | None
    baseline_observable_id: str | None
    morphology_observable_id: str | None
    joint_covariance_id: str | None
    joint_covariance_content_id: str | None
    normalizer_id: str | None
    parameter_labels: tuple[str, ...]
    baseline_response_replay_matrix: tuple[tuple[float, ...], ...] | None
    morphology_response_replay_matrix: tuple[tuple[float, ...], ...] | None
    joint_covariance_replay_matrix: tuple[tuple[float, ...], ...] | None
    relative_tolerance: float | None
    missing_inputs: tuple[str, ...]
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SCHUR_TOKEN:
            raise AnchoredResponseGeometryError(
                "SchurMorphologyInformationReport must be created by "
                "measure_schur_morphology_information"
            )
        if not isinstance(self.status, SchurMorphologyStatus):
            raise AnchoredResponseGeometryError(
                "status must be a SchurMorphologyStatus"
            )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise AnchoredResponseGeometryError(
                "Schur report must retain the registered claim boundary"
            )

    @property
    def exact_one_dimensional_reduction(self) -> bool:
        return bool(
            self.status is SchurMorphologyStatus.MEASURED
            and self.baseline_geometry is not None
            and self.conditional_morphology_geometry is not None
            and self.baseline_geometry.status is AnchoredResponseStatus.MEASURED
            and self.conditional_morphology_geometry.status
            is AnchoredResponseStatus.MEASURED
            and self.contraction is not None
            and self.contraction.parameter_dimension == 1
            and self.contraction.baseline_rank == 1
            and self.contraction.joint_rank == 1
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "baseline_geometry": (
                None
                if self.baseline_geometry is None
                else self.baseline_geometry.as_payload()
            ),
            "conditional_morphology_geometry": (
                None
                if self.conditional_morphology_geometry is None
                else self.conditional_morphology_geometry.as_payload()
            ),
            "baseline_information": [
                list(row) for row in self.baseline_information
            ],
            "incremental_information": [
                list(row) for row in self.incremental_information
            ],
            "joint_information": [list(row) for row in self.joint_information],
            "conditional_response": [
                list(row) for row in self.conditional_response
            ],
            "conditional_covariance": [
                list(row) for row in self.conditional_covariance
            ],
            "contraction": (
                None if self.contraction is None else self.contraction.as_payload()
            ),
            "baseline_observable_id": self.baseline_observable_id,
            "morphology_observable_id": self.morphology_observable_id,
            "joint_covariance_id": self.joint_covariance_id,
            "joint_covariance_content_id": self.joint_covariance_content_id,
            "normalizer_id": self.normalizer_id,
            "parameter_labels": list(self.parameter_labels),
            "relative_tolerance": self.relative_tolerance,
            "missing_inputs": list(self.missing_inputs),
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def measure_schur_morphology_information(
    *,
    baseline_response: object | None,
    morphology_response: object | None,
    joint_covariance: object | None,
    normalizer: NormalizerSpec | None,
    parameter_labels: Sequence[object] | None,
    transfer_id: str | None,
    transfer_source: TransferSource | str | None,
    transfer_spec: TransferFunctionSpec | None = None,
    mask_id: str | None,
    joint_covariance_id: str | None,
    baseline_observable_id: str | None,
    morphology_observable_id: str | None,
    rtol: float = 1.0e-12,
) -> SchurMorphologyInformationReport:
    """Measure conditional morphology information from one joint covariance."""

    missing = tuple(
        name
        for name, value in (
            ("baseline_response", baseline_response),
            ("morphology_response", morphology_response),
            ("joint_covariance", joint_covariance),
            ("normalizer", normalizer),
            ("parameter_labels", parameter_labels),
            ("transfer_id", transfer_id),
            ("transfer_source", transfer_source),
            ("mask_id", mask_id),
            ("joint_covariance_id", joint_covariance_id),
            ("baseline_observable_id", baseline_observable_id),
            ("morphology_observable_id", morphology_observable_id),
        )
        if value is None
    )
    if (
        normalizer is not None
        and normalizer.availability is not NormalizerAvailability.AVAILABLE
    ):
        missing = tuple(dict.fromkeys((*missing, "normalizer_available")))
    normalized_source = (
        None
        if transfer_source is None
        else _transfer_source(transfer_source)
    )
    canonical_spec = (
        None
        if transfer_spec is None
        else _canonical_transfer_spec(transfer_spec)
    )
    if normalized_source is TransferSource.NONE and canonical_spec is not None:
        raise AnchoredResponseGeometryError(
            "transfer_source=none must not carry TransferFunctionSpec"
        )
    if (
        normalized_source is not None
        and normalized_source is not TransferSource.NONE
        and canonical_spec is None
    ):
        missing = tuple(dict.fromkeys((*missing, "transfer_spec")))
    if (
        canonical_spec is not None
        and normalized_source is not None
        and canonical_spec.source is not normalized_source
    ):
        raise AnchoredResponseGeometryError(
            "transfer_source must match transfer_spec.source"
        )
    if (
        canonical_spec is not None
        and transfer_id is not None
        and canonical_spec.transfer_id != transfer_id
    ):
        raise AnchoredResponseGeometryError(
            "transfer_id must match transfer_spec.transfer_id"
        )
    if missing:
        for name, value in (
            ("transfer_id", transfer_id),
            ("transfer_source", transfer_source),
            ("mask_id", mask_id),
            ("joint_covariance_id", joint_covariance_id),
            ("baseline_observable_id", baseline_observable_id),
            ("morphology_observable_id", morphology_observable_id),
        ):
            if value is not None:
                if name == "transfer_source":
                    _transfer_source(value)
                elif (
                    name == "transfer_id"
                    and (
                        (
                            normalized_source is not None
                            and normalized_source is not TransferSource.NONE
                        )
                        or canonical_spec is not None
                    )
                ):
                    _text(value, name)
                else:
                    _receipt(value, name)
        return SchurMorphologyInformationReport(
            status=SchurMorphologyStatus.MISSING_INPUT,
            baseline_geometry=None,
            conditional_morphology_geometry=None,
            baseline_information=(),
            incremental_information=(),
            joint_information=(),
            conditional_response=(),
            conditional_covariance=(),
            contraction=None,
            baseline_observable_id=baseline_observable_id,
            morphology_observable_id=morphology_observable_id,
            joint_covariance_id=joint_covariance_id,
            joint_covariance_content_id=None,
            normalizer_id=(
                None if normalizer is None else normalizer.normalizer_id
            ),
            parameter_labels=(),
            baseline_response_replay_matrix=None,
            morphology_response_replay_matrix=None,
            joint_covariance_replay_matrix=None,
            relative_tolerance=None,
            missing_inputs=missing,
            _construction_token=_SCHUR_TOKEN,
        )

    tolerance = _relative_tolerance(rtol)
    labels = _texts(parameter_labels, "parameter_labels")
    baseline = _array(baseline_response, "baseline_response", ndim=2)
    morphology = _array(morphology_response, "morphology_response", ndim=2)
    if baseline.shape[0] == 0 or morphology.shape[0] == 0:
        raise AnchoredResponseGeometryError(
            "baseline and morphology responses must have positive row counts"
        )
    if baseline.shape[1] != len(labels) or morphology.shape[1] != len(labels):
        raise AnchoredResponseGeometryError(
            "both response column counts must match parameter_labels"
        )
    scaling = _normalizer_matrix(normalizer, labels)
    del scaling
    transfer, source, canonical_spec = _transfer_binding(
        transfer_id=transfer_id,
        transfer_source=transfer_source,
        transfer_spec=transfer_spec,
    )
    mask = _receipt(mask_id, "mask_id")
    covariance_receipt = _receipt(
        joint_covariance_id, "joint_covariance_id"
    )
    baseline_id = _receipt(
        baseline_observable_id, "baseline_observable_id"
    )
    morphology_id = _receipt(
        morphology_observable_id, "morphology_observable_id"
    )
    total = baseline.shape[0] + morphology.shape[0]
    (
        covariance_matrix,
        _,
        _,
        covariance_tolerance,
        _,
        supported_joint_standardized,
    ) = _covariance_support(
        joint_covariance,
        dimension=total,
        rtol=tolerance,
    )
    joint_covariance_content_id = _array_content_identity(covariance_matrix)
    if covariance_receipt != joint_covariance_content_id:
        raise AnchoredResponseGeometryError(
            "joint_covariance_id must match the canonical joint covariance "
            "content identity"
        )
    baseline_rows = baseline.shape[0]
    c_bb = covariance_matrix[:baseline_rows, :baseline_rows]
    c_mm = covariance_matrix[baseline_rows:, baseline_rows:]
    # Form the generalized Schur complement in standardized observable
    # coordinates. This makes a diagonal change of observable units a
    # congruence transformation rather than a change in inferred information.
    baseline_scale = np.where(
        np.diag(c_bb) > 0.0,
        np.sqrt(np.diag(c_bb)),
        1.0,
    )
    morphology_scale = np.where(
        np.diag(c_mm) > 0.0,
        np.sqrt(np.diag(c_mm)),
        1.0,
    )
    # Partition the already-truncated joint supported covariance.  Deriving
    # the Schur blocks from the untruncated covariance can normalize a joint
    # null mode back above threshold in a lower-dimensional conditional
    # block.  The support decision therefore happens exactly once, before
    # conditioning, and is inherited by every downstream block.
    c_bb_standardized = supported_joint_standardized[
        :baseline_rows, :baseline_rows
    ]
    c_bm_standardized = supported_joint_standardized[
        :baseline_rows, baseline_rows:
    ]
    c_mb_standardized = c_bm_standardized.T
    c_mm_standardized = supported_joint_standardized[
        baseline_rows:, baseline_rows:
    ]
    c_bb_pinv = np.linalg.pinv(
        c_bb_standardized,
        rcond=tolerance,
        hermitian=True,
    )
    projected_cross = (
        c_bb_standardized @ c_bb_pinv @ c_bm_standardized
    )
    range_tolerance = max(
        100.0 * tolerance,
        256.0
        * np.finfo(float).eps
        * max(total, 1) ** 2,
    )
    if not np.allclose(
        projected_cross,
        c_bm_standardized,
        rtol=0.0,
        atol=range_tolerance,
    ):
        raise AnchoredResponseGeometryError(
            "joint covariance cross block lies outside baseline covariance "
            "range; generalized Schur complement is not licensed"
        )
    baseline_standardized = baseline / baseline_scale[:, None]
    morphology_standardized = morphology / morphology_scale[:, None]
    conditional_response_standardized = (
        morphology_standardized
        - c_mb_standardized @ c_bb_pinv @ baseline_standardized
    )
    conditional_covariance_standardized = (
        c_mm_standardized
        - c_mb_standardized @ c_bb_pinv @ c_bm_standardized
    )
    conditional_covariance_standardized = 0.5 * (
        conditional_covariance_standardized
        + conditional_covariance_standardized.T
    )
    conditional_values, conditional_vectors = np.linalg.eigh(
        conditional_covariance_standardized
    )
    conditional_spectral_scale = float(
        np.max(np.abs(conditional_values), initial=0.0)
    )
    conditional_psd_tolerance = (
        256.0
        * np.finfo(float).eps
        * max(morphology.shape[0], 1) ** 2
        * max(conditional_spectral_scale, 1.0)
    )
    if (
        conditional_values.size
        and float(np.min(conditional_values)) < -conditional_psd_tolerance
    ):
        raise AnchoredResponseGeometryError(
            "joint covariance produced a non-positive-semidefinite "
            "conditional covariance"
        )
    conditional_support = conditional_values > covariance_tolerance
    if not np.all(conditional_support):
        # The public rtol declares one support quotient for the joint
        # covariance. A scalar or lower-dimensional Schur block must not
        # normalize an excluded joint mode back to unit variance and re-admit
        # it as information. Preserve well-conditioned bytes by reconstructing
        # only when the inherited joint cutoff actually removes a mode.
        retained_values = np.where(
            conditional_support,
            np.maximum(conditional_values, 0.0),
            0.0,
        )
        conditional_covariance_standardized = (
            conditional_vectors
            @ np.diag(retained_values)
            @ conditional_vectors.T
        )
    conditional_response = (
        morphology_scale[:, None] * conditional_response_standardized
    )
    conditional_covariance = (
        morphology_scale[:, None]
        * conditional_covariance_standardized
        * morphology_scale[None, :]
    )
    conditional_covariance = 0.5 * (
        conditional_covariance + conditional_covariance.T
    )
    del covariance_tolerance

    baseline_geometry = measure_anchored_response_geometry(
        response=baseline,
        covariance=c_bb,
        normalizer=normalizer,
        parameter_labels=labels,
        transfer_id=transfer,
        transfer_source=source,
        transfer_spec=canonical_spec,
        mask_id=mask,
        covariance_id=_array_content_identity(c_bb),
        rtol=tolerance,
    )
    conditional_geometry = measure_anchored_response_geometry(
        response=conditional_response,
        covariance=conditional_covariance,
        normalizer=normalizer,
        parameter_labels=labels,
        transfer_id=transfer,
        transfer_source=source,
        transfer_spec=canonical_spec,
        mask_id=mask,
        covariance_id=_array_content_identity(conditional_covariance),
        rtol=tolerance,
    )
    baseline_anchored = (
        np.zeros((0, len(labels)), dtype=float)
        if not baseline_geometry.anchored_response_replay_matrix
        else _array(
            baseline_geometry.anchored_response_replay_matrix,
            "baseline anchored response",
            ndim=2,
        )
    )
    conditional_anchored = (
        np.zeros((0, len(labels)), dtype=float)
        if not conditional_geometry.anchored_response_replay_matrix
        else _array(
            conditional_geometry.anchored_response_replay_matrix,
            "conditional anchored response",
            ndim=2,
        )
    )
    baseline_information = baseline_anchored.T @ baseline_anchored
    incremental_information = conditional_anchored.T @ conditional_anchored
    joint_information = baseline_information + incremental_information
    contraction = _identified_set_contraction(
        baseline_information,
        joint_information,
        rtol=tolerance,
    )
    statuses = {
        baseline_geometry.status,
        conditional_geometry.status,
    }
    if AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT in statuses:
        status = SchurMorphologyStatus.OUTSIDE_SUPPORTED_QUOTIENT
    elif AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE in statuses:
        status = SchurMorphologyStatus.EXPLICIT_NULL_RESPONSE
    else:
        status = SchurMorphologyStatus.MEASURED
    return SchurMorphologyInformationReport(
        status=status,
        baseline_geometry=baseline_geometry,
        conditional_morphology_geometry=conditional_geometry,
        baseline_information=_matrix_tuple(baseline_information),
        incremental_information=_matrix_tuple(incremental_information),
        joint_information=_matrix_tuple(joint_information),
        conditional_response=_matrix_tuple(conditional_response),
        conditional_covariance=_matrix_tuple(conditional_covariance),
        contraction=contraction,
        baseline_observable_id=baseline_id,
        morphology_observable_id=morphology_id,
        joint_covariance_id=covariance_receipt,
        joint_covariance_content_id=joint_covariance_content_id,
        normalizer_id=normalizer.normalizer_id,
        parameter_labels=labels,
        baseline_response_replay_matrix=_matrix_tuple(baseline),
        morphology_response_replay_matrix=_matrix_tuple(morphology),
        joint_covariance_replay_matrix=_matrix_tuple(covariance_matrix),
        relative_tolerance=tolerance,
        missing_inputs=(),
        _construction_token=_SCHUR_TOKEN,
    )


def revalidate_schur_morphology_information(
    report: SchurMorphologyInformationReport,
    *,
    normalizer: NormalizerSpec,
) -> SchurMorphologyInformationReport:
    """Recompute a Schur report from its exact replay matrices."""

    if type(report) is not SchurMorphologyInformationReport:
        raise AnchoredResponseGeometryError(
            "report must be an exact factory-derived "
            "SchurMorphologyInformationReport"
        )
    if report.status is SchurMorphologyStatus.MISSING_INPUT:
        return report
    rebuilt = measure_schur_morphology_information(
        baseline_response=report.baseline_response_replay_matrix,
        morphology_response=report.morphology_response_replay_matrix,
        joint_covariance=report.joint_covariance_replay_matrix,
        normalizer=normalizer,
        parameter_labels=report.parameter_labels,
        transfer_id=report.baseline_geometry.transfer_id,
        transfer_source=report.baseline_geometry.transfer_source,
        transfer_spec=report.baseline_geometry.transfer_spec,
        mask_id=report.baseline_geometry.mask_id,
        joint_covariance_id=report.joint_covariance_id,
        baseline_observable_id=report.baseline_observable_id,
        morphology_observable_id=report.morphology_observable_id,
        rtol=report.relative_tolerance,
    )
    if rebuilt != report:
        raise AnchoredResponseGeometryError(
            "report fields do not match replayed Schur geometry"
        )
    return rebuilt


def _phase_status(
    gauge: AnchorGaugeInterval,
    nonlinearity: NonlinearityReport,
) -> NonlinearityPhaseStatus:
    if gauge.lower is None or gauge.upper is None:
        return NonlinearityPhaseStatus.ANCHOR_UNAVAILABLE
    attribution = nonlinearity.attribution_status
    if attribution is NonlinearityAttributionStatus.MISSING_RESPONSE:
        return NonlinearityPhaseStatus.MISSING_RESPONSE
    if attribution is NonlinearityAttributionStatus.NON_IDENTIFIED_RESPONSE:
        return NonlinearityPhaseStatus.NON_IDENTIFIED_RESPONSE
    if attribution is NonlinearityAttributionStatus.OUTSIDE_SUPPORTED_QUOTIENT:
        return NonlinearityPhaseStatus.OUTSIDE_SUPPORTED_QUOTIENT
    if attribution is NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD:
        return NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD
    if gauge.lower <= 1.0 < gauge.upper:
        return NonlinearityPhaseStatus.ANCHOR_INTERVAL_STRADDLES_BOUNDARY
    exceeded = gauge.lower > 1.0
    if attribution is NonlinearityAttributionStatus.LINEAR_COMPATIBLE:
        return (
            NonlinearityPhaseStatus.LINEAR_PREMISE_MISMATCH
            if exceeded
            else NonlinearityPhaseStatus.LINEAR_PREMISE_COMPATIBLE
        )
    if attribution is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE:
        return (
            NonlinearityPhaseStatus.NONLINEAR_AND_EXCEEDANCE
            if exceeded
            else NonlinearityPhaseStatus.NONLINEAR_WITHIN_ANCHOR
        )
    return NonlinearityPhaseStatus.UNATTRIBUTED_OFF_MANIFOLD


def _nonlinear_candidate_gain_payload(
    nonlinearity: NonlinearityReport,
) -> list[dict[str, object]]:
    """Expose score gains without turning them into evidence or coverage."""

    controls = tuple(
        candidate
        for candidate in nonlinearity.candidate_comparisons
        if candidate.kind is not CandidateKind.NONLINEAR
    )
    nonlinear = tuple(
        candidate
        for candidate in nonlinearity.candidate_comparisons
        if candidate.kind is CandidateKind.NONLINEAR
    )
    if not controls:
        return []
    held_out_control = max(candidate.held_out_score for candidate in controls)
    matched_control = max(
        candidate.matched_injection_score for candidate in controls
    )
    margin = nonlinearity.nonlinear_gain_margin
    return [
        {
            "candidate_id": candidate.candidate_id,
            "scoring_rule": candidate.scoring_rule.value,
            "held_out_gain_over_best_control": (
                candidate.held_out_score - held_out_control
            ),
            "matched_injection_gain_over_best_control": (
                candidate.matched_injection_score - matched_control
            ),
            "registered_gain_margin": margin,
            "clears_both_registered_margins": (
                margin is not None
                and candidate.held_out_score - held_out_control >= margin
                and candidate.matched_injection_score - matched_control >= margin
            ),
        }
        for candidate in nonlinear
    ]


@dataclass(frozen=True)
class NonlinearityPhaseCell:
    cell_id: str
    dgp_kind: NonlinearityDGPKind
    anchor_gauge: AnchorGaugeInterval
    nonlinearity: NonlinearityReport
    status: NonlinearityPhaseStatus
    premise_exceeded: bool | None
    stress_used_for_attribution: bool
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PHASE_CELL_TOKEN:
            raise AnchoredResponseGeometryError(
                "NonlinearityPhaseCell must be created by "
                "build_nonlinearity_phase_cell"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "cell_id": self.cell_id,
            "dgp_kind": self.dgp_kind.value,
            "anchor_gauge": self.anchor_gauge.as_payload(),
            "nonlinearity_status": self.nonlinearity.attribution_status.value,
            "nonlinearity_analysis_id": self.nonlinearity.analysis_id,
            "held_out_receipt": self.nonlinearity.held_out_receipt,
            "matched_injection_receipt": (
                self.nonlinearity.matched_injection_receipt
            ),
            "candidate_evaluation_ids": [
                candidate.evaluation_id
                for candidate in self.nonlinearity.candidate_comparisons
            ],
            "t_parallel": self.nonlinearity.tangent_statistic,
            "t_perp": self.nonlinearity.perpendicular_statistic,
            "delta_nl": self.nonlinearity.delta_nl,
            "delta_nl_status": (
                "DEFINED"
                if self.nonlinearity.delta_nl is not None
                else "NOT_COMPUTED_NO_NONLINEAR_MANIFOLD_DISTANCE"
            ),
            "null_residual_sq": self.nonlinearity.null_residual_sq,
            "nonlinear_candidate_gains": _nonlinear_candidate_gain_payload(
                self.nonlinearity
            ),
            "status": self.status.value,
            "premise_exceeded": self.premise_exceeded,
            "stress_used_for_attribution": self.stress_used_for_attribution,
        }


def build_nonlinearity_phase_cell(
    *,
    cell_id: str,
    dgp_kind: NonlinearityDGPKind,
    anchor_gauge: AnchorGaugeInterval,
    nonlinearity: NonlinearityReport,
) -> NonlinearityPhaseCell:
    """Combine, but never convert between, stress and attribution reports."""

    _text(cell_id, "cell_id")
    if not isinstance(dgp_kind, NonlinearityDGPKind):
        raise AnchoredResponseGeometryError(
            "dgp_kind must be a NonlinearityDGPKind"
        )
    if type(anchor_gauge) is not AnchorGaugeInterval:
        raise AnchoredResponseGeometryError(
            "anchor_gauge must be an AnchorGaugeInterval"
        )
    try:
        canonical_gauge = AnchorGaugeInterval(
            anchor_id=anchor_gauge.anchor_id,
            vector_id=anchor_gauge.vector_id,
            lower=anchor_gauge.lower,
            upper=anchor_gauge.upper,
            status=anchor_gauge.status,
            conditional_values=anchor_gauge.conditional_values,
            assumptions=anchor_gauge.assumptions,
            allowed_use=anchor_gauge.allowed_use,
            forbidden_use=anchor_gauge.forbidden_use,
        )
    except AttributeError as exc:
        raise AnchoredResponseGeometryError(
            "anchor_gauge is missing validated fields"
        ) from exc
    if canonical_gauge != anchor_gauge:
        raise AnchoredResponseGeometryError(
            "anchor_gauge fields do not match constructor invariants"
        )
    validated = revalidate_nonlinearity_report(nonlinearity)
    premise_exceeded = (
        None
        if anchor_gauge.lower is None
        or anchor_gauge.upper is None
        or anchor_gauge.lower <= 1.0 < anchor_gauge.upper
        else anchor_gauge.lower > 1.0
    )
    return NonlinearityPhaseCell(
        cell_id=cell_id,
        dgp_kind=dgp_kind,
        anchor_gauge=canonical_gauge,
        nonlinearity=validated,
        status=_phase_status(anchor_gauge, validated),
        premise_exceeded=premise_exceeded,
        stress_used_for_attribution=False,
        _construction_token=_PHASE_CELL_TOKEN,
    )


def _revalidated_phase_cell(value: object) -> NonlinearityPhaseCell:
    if type(value) is not NonlinearityPhaseCell:
        raise AnchoredResponseGeometryError(
            "cells must be exact factory-derived NonlinearityPhaseCell values"
        )
    try:
        canonical = build_nonlinearity_phase_cell(
            cell_id=value.cell_id,
            dgp_kind=value.dgp_kind,
            anchor_gauge=value.anchor_gauge,
            nonlinearity=value.nonlinearity,
        )
    except AttributeError as exc:
        raise AnchoredResponseGeometryError(
            "NonlinearityPhaseCell is missing factory-validated fields"
        ) from exc
    if canonical != value:
        raise AnchoredResponseGeometryError(
            "NonlinearityPhaseCell fields do not match the factory-derived "
            "stress and attribution result"
        )
    return canonical


@dataclass(frozen=True)
class NonlinearityPhaseDiagramReport:
    cells: tuple[NonlinearityPhaseCell, ...]
    master_seed: int
    data_source: str
    transfer_id: str
    transfer_source: TransferSource
    transfer_spec: TransferFunctionSpec | None
    pr151_data_used: bool
    forced_classification: bool
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PHASE_DIAGRAM_TOKEN:
            raise AnchoredResponseGeometryError(
                "NonlinearityPhaseDiagramReport must be created by "
                "build_nonlinearity_phase_diagram"
            )
        if not isinstance(self.transfer_source, TransferSource):
            raise AnchoredResponseGeometryError(
                "phase-diagram transfer_source must be a TransferSource"
            )
        _receipt(self.transfer_id, "phase_diagram.transfer_id")
        if self.transfer_source is TransferSource.NONE:
            if self.transfer_spec is not None:
                raise AnchoredResponseGeometryError(
                    "transfer_source=none must not carry TransferFunctionSpec"
                )
        else:
            canonical_spec = _canonical_transfer_spec(self.transfer_spec)
            if (
                canonical_spec.source is not self.transfer_source
                or canonical_spec.transfer_id != self.transfer_id
            ):
                raise AnchoredResponseGeometryError(
                    "phase-diagram transfer provenance fields must match"
                )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise AnchoredResponseGeometryError(
                "phase diagram must retain the registered claim boundary"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "cells": [cell.as_payload() for cell in self.cells],
            "master_seed": self.master_seed,
            "data_source": self.data_source,
            "transfer_id": self.transfer_id,
            "transfer_source": self.transfer_source.value,
            "transfer_metadata": (
                None
                if self.transfer_spec is None
                else self.transfer_spec.to_metadata()
            ),
            "pr151_data_used": self.pr151_data_used,
            "forced_classification": self.forced_classification,
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def build_nonlinearity_phase_diagram(
    *,
    cells: Sequence[NonlinearityPhaseCell],
    master_seed: int,
    transfer_id: str,
    transfer_source: TransferSource | str,
    transfer_spec: TransferFunctionSpec | None = None,
    data_source: str = "synthetic_only",
    pr151_data_used: bool = False,
) -> NonlinearityPhaseDiagramReport:
    """Build the preregistered eight-cell synthetic phase diagram."""

    if isinstance(master_seed, bool) or not isinstance(master_seed, int):
        raise AnchoredResponseGeometryError("master_seed must be an integer")
    if master_seed != 20260728:
        raise AnchoredResponseGeometryError(
            "PR-255 phase diagram must use master seed 20260728"
        )
    if data_source != "synthetic_only":
        raise AnchoredResponseGeometryError(
            "PR-255 phase diagram is synthetic-only"
        )
    if pr151_data_used is not False:
        raise AnchoredResponseGeometryError(
            "PR-151 partial data is forbidden in the PR-255 phase diagram"
        )
    source = _transfer_source(transfer_source)
    transfer = _receipt(transfer_id, "transfer_id")
    canonical_spec = (
        None
        if transfer_spec is None
        else _canonical_transfer_spec(transfer_spec)
    )
    if source is TransferSource.NONE:
        if canonical_spec is not None:
            raise AnchoredResponseGeometryError(
                "transfer_source=none must not carry TransferFunctionSpec"
            )
    elif canonical_spec is None:
        raise AnchoredResponseGeometryError(
            "non-none phase-diagram transfer sources require "
            "TransferFunctionSpec"
        )
    elif canonical_spec.source is not source:
        raise AnchoredResponseGeometryError(
            "phase-diagram transfer_source must match transfer_spec.source"
        )
    elif canonical_spec.transfer_id != transfer:
        raise AnchoredResponseGeometryError(
            "phase-diagram transfer_id must match transfer_spec.transfer_id"
        )
    values = tuple(_revalidated_phase_cell(value) for value in cells)
    if len({value.cell_id for value in values}) != len(values):
        raise AnchoredResponseGeometryError("phase cell ids must be unique")
    kinds = tuple(value.dgp_kind for value in values)
    if set(kinds) != set(NonlinearityDGPKind) or len(kinds) != len(
        NonlinearityDGPKind
    ):
        raise AnchoredResponseGeometryError(
            "phase diagram requires exactly one cell for every registered DGP"
        )
    mismatched = tuple(
        value.cell_id
        for value in values
        if value.nonlinearity.response_rank.transfer_id != transfer
    )
    if mismatched:
        raise AnchoredResponseGeometryError(
            "phase-cell transfer identities do not match the registered "
            f"phase-diagram transfer identity: {mismatched}"
        )
    return NonlinearityPhaseDiagramReport(
        cells=values,
        master_seed=master_seed,
        data_source=data_source,
        transfer_id=transfer,
        transfer_source=source,
        transfer_spec=canonical_spec,
        pr151_data_used=False,
        forced_classification=False,
        _construction_token=_PHASE_DIAGRAM_TOKEN,
    )


__all__ = [
    "AnchoredResponseGeometryError",
    "AnchoredResponseGeometryReport",
    "AnchoredResponseStatus",
    "IdentifiedSetContractionReport",
    "IdentifiedSetContractionStatus",
    "NonlinearityDGPKind",
    "NonlinearityPhaseCell",
    "NonlinearityPhaseDiagramReport",
    "NonlinearityPhaseStatus",
    "PrincipalAngleReport",
    "PrincipalAngleStatus",
    "SchurMorphologyInformationReport",
    "SchurMorphologyStatus",
    "anchored_numeric_content_id",
    "build_nonlinearity_phase_cell",
    "build_nonlinearity_phase_diagram",
    "measure_anchored_response_geometry",
    "measure_schur_morphology_information",
    "revalidate_anchored_response_geometry",
    "revalidate_schur_morphology_information",
]

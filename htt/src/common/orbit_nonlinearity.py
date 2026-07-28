"""Typed O(3), response-rank, and off-manifold diagnostic contracts.

The objects in this module keep three questions separate:

* how an irreducible departure state transforms under O(3);
* what rank is supported by a supplied transfer/mask/covariance response; and
* whether an observed residual lies outside the registered linear tangent
  space, and, if so, whether a held-out nonlinear candidate defeats every
  registered alternative.

These are pre-solver diagnostics.  They do not identify a Bianchi family,
detect a geometry, or turn morphology compatibility into likelihood evidence.
"""

from __future__ import annotations

import math
import hashlib
import json
from dataclasses import InitVar, dataclass
from enum import Enum
from numbers import Real
from typing import Sequence

import numpy as np

from common.statistical_foundations import DepartureState


class OrbitNonlinearityError(ValueError):
    """Raised when an orbit or discrepancy contract is incomplete."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class VectorParity(_StringEnum):
    POLAR = "POLAR"
    AXIAL = "AXIAL"


class ResponseRankStatus(_StringEnum):
    MEASURED = "MEASURED"
    MISSING_INPUT = "MISSING_INPUT"


class CandidateKind(_StringEnum):
    NONLINEAR = "NONLINEAR"
    LINEAR = "LINEAR"
    SYSTEMATICS = "SYSTEMATICS"
    FRAME_MISMATCH = "FRAME_MISMATCH"
    DERIVATIVE_FAILURE = "DERIVATIVE_FAILURE"


class CandidateScoringRule(_StringEnum):
    """Registered score whose values are derived from bound arrays."""

    NEGATIVE_MEAN_SQUARED_ERROR = "NEGATIVE_MEAN_SQUARED_ERROR_V1"


class NonlinearityAttributionStatus(_StringEnum):
    LINEAR_COMPATIBLE = "LINEAR_COMPATIBLE"
    NONLINEAR_COMPATIBLE = "NONLINEAR_COMPATIBLE"
    NON_IDENTIFIED_RESPONSE = "NON_IDENTIFIED_RESPONSE"
    UNATTRIBUTED_OFF_MANIFOLD = "UNATTRIBUTED_OFF_MANIFOLD"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"
    MISSING_RESPONSE = "MISSING_RESPONSE"


STF5_CARTESIAN_BASIS = "STF5_CARTESIAN_XX_YY_XY_XZ_YZ_V1"
DEPARTURE_O3_PARITY = (
    "SIGMA_STF2;OMEGA_AXIAL;BETA_POLAR;DELTA_OMEGA_K_SCALAR"
)
DEPARTURE_O3_UNITS = "dimensionless"
ACTIVE_O3_CONVENTION = "ACTIVE_CARTESIAN_COMPONENT_ACTION_V1"
FOUND_EQUIV_STATUS = "ACTIVE_CONDITIONAL"
FOUND_EQUIV_PREREQUISITE = "EGS3-B1"
PR251_INVARIANT_NAMES = (
    "tr_sigma2",
    "tr_sigma3",
    "beta2",
    "beta_sigma_beta",
    "beta_sigma2_beta",
    "det_beta_sigma_beta_sigma2_beta",
)
_REQUIRED_ALTERNATIVES = frozenset(
    {
        CandidateKind.LINEAR,
        CandidateKind.SYSTEMATICS,
        CandidateKind.FRAME_MISMATCH,
        CandidateKind.DERIVATIVE_FAILURE,
    }
)
_DIAGNOSTIC_ALLOWED_USE = (
    "pre-solver response-rank diagnostic",
    "orbit-invariant morphology compatibility",
    "held-out model-discrepancy diagnostic",
)
_DIAGNOSTIC_FORBIDDEN_USE = (
    "Bianchi family identification",
    "geometry detection",
    "native solver result",
    "posterior or evidence term",
)
_RANK_REPORT_TOKEN = object()
_NONLINEARITY_REPORT_TOKEN = object()
_ORBIT_REPORT_TOKEN = object()
_CANDIDATE_EVALUATION_TOKEN = object()
_CANDIDATE_INDEPENDENCE_TOKEN = object()


def _contains_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "b":
            return True
        if value.dtype.kind == "O":
            return any(_contains_bool(item) for item in value.flat)
        return False
    if isinstance(value, (tuple, list)):
        return any(_contains_bool(item) for item in value)
    return False


def _contains_complex(value: object) -> bool:
    if isinstance(value, (complex, np.complexfloating)):
        return True
    if isinstance(value, np.ndarray):
        if value.dtype.kind == "c":
            return True
        if value.dtype.kind == "O":
            return any(_contains_complex(item) for item in value.flat)
        return False
    if isinstance(value, (tuple, list)):
        return any(_contains_complex(item) for item in value)
    return False


def _contains_text(value: object) -> bool:
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        return True
    if isinstance(value, np.ndarray):
        if value.dtype.kind in {"U", "S"}:
            return True
        if value.dtype.kind == "O":
            return any(_contains_text(item) for item in value.flat)
        return False
    if isinstance(value, (tuple, list)):
        return any(_contains_text(item) for item in value)
    return False


def _array(
    value: object,
    name: str,
    *,
    ndim: int | None = None,
    shape: tuple[int, ...] | None = None,
) -> np.ndarray:
    if _contains_bool(value):
        raise OrbitNonlinearityError(f"{name} must not contain booleans")
    if _contains_complex(value):
        raise OrbitNonlinearityError(f"{name} must be real, not complex")
    if _contains_text(value):
        raise OrbitNonlinearityError(f"{name} must be numeric, not text")
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise OrbitNonlinearityError(f"{name} must be numeric") from exc
    if ndim is not None and out.ndim != ndim:
        raise OrbitNonlinearityError(f"{name} must have ndim={ndim}")
    if shape is not None and out.shape != shape:
        raise OrbitNonlinearityError(
            f"{name} must have shape {shape}, got {out.shape}"
        )
    if not np.isfinite(out).all():
        raise OrbitNonlinearityError(f"{name} must be finite")
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise OrbitNonlinearityError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise OrbitNonlinearityError(f"{name} must be real, not complex")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise OrbitNonlinearityError(f"{name} must be numeric, not text")
    if not isinstance(value, Real):
        raise OrbitNonlinearityError(f"{name} must be a real number")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise OrbitNonlinearityError(f"{name} must be a real number") from exc
    if not math.isfinite(out):
        raise OrbitNonlinearityError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise OrbitNonlinearityError(f"{name} must be non-negative")
    return out


def _positive(value: object, name: str) -> float:
    out = _nonnegative(value, name)
    if out == 0.0:
        raise OrbitNonlinearityError(f"{name} must be positive")
    return out


def _relative_tolerance(value: object, name: str = "rtol") -> float:
    out = _positive(value, name)
    if out > 1.0e-3:
        raise OrbitNonlinearityError(
            f"{name} must be at most 1e-3 for rank/covariance decisions"
        )
    return out


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise OrbitNonlinearityError(f"{name} must be non-empty trimmed text")
    return value


def _evidence_receipt(value: object, name: str) -> str:
    out = _text(value, name)
    prefix = "sha256:"
    digest = out[len(prefix) :] if out.startswith(prefix) else ""
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise OrbitNonlinearityError(
            f"{name} must be a lowercase sha256 content identity"
        )
    return out


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise OrbitNonlinearityError(f"{name} must be a sequence")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise OrbitNonlinearityError(f"{name} must not be empty")
    if len(set(out)) != len(out):
        raise OrbitNonlinearityError(f"{name} must not contain duplicates")
    return out


def _diagnostic_lanes(
    allowed_use: Sequence[object],
    forbidden_use: Sequence[object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    allowed = _texts(allowed_use, "allowed_use")
    forbidden = _texts(forbidden_use, "forbidden_use")
    if allowed != _DIAGNOSTIC_ALLOWED_USE:
        raise OrbitNonlinearityError(
            "allowed_use must match the registered diagnostic lane"
        )
    if forbidden != _DIAGNOSTIC_FORBIDDEN_USE:
        raise OrbitNonlinearityError(
            "forbidden_use must match the registered claim firewall"
        )
    return allowed, forbidden


def _matrix_tuple(matrix: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in matrix)


def _array_content_identity(value: np.ndarray) -> str:
    """Return a role-independent identity for one accepted float64 array.

    Role labels belong to the enclosing evaluation receipt.  Including them
    here would let identical bytes masquerade as independent evidence merely
    by renaming their role.
    """

    array = np.ascontiguousarray(value, dtype="<f8")
    header = json.dumps(
        {
            "dtype": "<f8",
            "schema": "HTT_NUMERIC_ARRAY_V1",
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


@dataclass(frozen=True)
class OrientedDirection:
    """An oriented unit direction; ``v`` and ``-v`` are distinct."""

    vector: tuple[float, float, float]
    parity: VectorParity

    def __post_init__(self) -> None:
        vector = _array(self.vector, "vector", shape=(3,))
        scale = float(np.max(np.abs(vector)))
        if scale == 0.0:
            raise OrbitNonlinearityError("vector must be non-zero")
        scaled = vector / scale
        norm = float(np.linalg.norm(scaled))
        if not math.isfinite(norm) or norm == 0.0:
            raise OrbitNonlinearityError("vector cannot be normalized safely")
        if not isinstance(self.parity, VectorParity):
            raise OrbitNonlinearityError("parity must be a VectorParity")
        unit = scaled / norm
        object.__setattr__(
            self, "vector", tuple(float(value) for value in unit)
        )

    def signed_dot(self, other: "OrientedDirection") -> float:
        if not isinstance(other, OrientedDirection):
            raise TypeError("other must be an OrientedDirection")
        if other.parity is not self.parity:
            raise OrbitNonlinearityError(
                "signed dot requires matching polar/axial parity"
            )
        return float(
            np.clip(np.dot(self.vector, other.vector), -1.0, 1.0)
        )


@dataclass(frozen=True)
class O3Transform:
    """A frozen proper or improper orthogonal transformation."""

    matrix: tuple[tuple[float, float, float], ...]
    transform_id: str
    coordinate_frame: str
    action_convention: str = ACTIVE_O3_CONVENTION
    atol: float = 1e-10

    def __post_init__(self) -> None:
        matrix = _array(self.matrix, "matrix", shape=(3, 3))
        atol = _positive(self.atol, "atol")
        if atol > 1.0e-6:
            raise OrbitNonlinearityError(
                "atol must be at most 1e-6 for an O(3) contract"
            )
        if not np.allclose(
            matrix.T @ matrix, np.eye(3), atol=atol, rtol=0.0
        ):
            raise OrbitNonlinearityError("matrix must be orthogonal")
        determinant = float(np.linalg.det(matrix))
        if not math.isclose(abs(determinant), 1.0, abs_tol=atol, rel_tol=0.0):
            raise OrbitNonlinearityError("matrix determinant must be +/-1")
        object.__setattr__(self, "matrix", _matrix_tuple(matrix))
        object.__setattr__(self, "atol", atol)
        _text(self.transform_id, "transform_id")
        _text(self.coordinate_frame, "coordinate_frame")
        if self.action_convention != ACTIVE_O3_CONVENTION:
            raise OrbitNonlinearityError(
                "action_convention must use the registered active action"
            )

    @property
    def determinant(self) -> int:
        return 1 if np.linalg.det(np.asarray(self.matrix)) > 0.0 else -1

    def apply_direction(self, direction: OrientedDirection) -> OrientedDirection:
        if not isinstance(direction, OrientedDirection):
            raise TypeError("direction must be an OrientedDirection")
        matrix = np.asarray(self.matrix)
        vector = matrix @ np.asarray(direction.vector)
        if direction.parity is VectorParity.AXIAL:
            vector = self.determinant * vector
        return OrientedDirection(tuple(vector), direction.parity)


def stf5_to_matrix(values: Sequence[object]) -> np.ndarray:
    """Decode ``(Sxx,Syy,Sxy,Sxz,Syz)`` with ``Szz=-Sxx-Syy``."""

    vector = _array(values, "sigma_ab", shape=(5,))
    xx, yy, xy, xz, yz = vector
    return np.array(
        (
            (xx, xy, xz),
            (xy, yy, yz),
            (xz, yz, -xx - yy),
        ),
        dtype=float,
    )


def matrix_to_stf5(matrix: object) -> tuple[float, ...]:
    value = _array(matrix, "sigma_matrix", shape=(3, 3))
    scale = float(np.max(np.abs(value), initial=0.0))
    tolerance = 64.0 * np.finfo(float).eps * scale
    if not np.allclose(value, value.T, atol=tolerance, rtol=0.0):
        raise OrbitNonlinearityError("sigma_matrix must be symmetric")
    if not math.isclose(
        float(np.trace(value)), 0.0, abs_tol=tolerance, rel_tol=0.0
    ):
        raise OrbitNonlinearityError("sigma_matrix must be trace-free")
    return (
        float(value[0, 0]),
        float(value[1, 1]),
        float(value[0, 1]),
        float(value[0, 2]),
        float(value[1, 2]),
    )


def transform_departure_state(
    state: DepartureState,
    transform: O3Transform,
) -> DepartureState:
    """Apply the declared polar/axial O(3) action to one state."""

    if not isinstance(state, DepartureState):
        raise TypeError("state must be a DepartureState")
    if not isinstance(transform, O3Transform):
        raise TypeError("transform must be an O3Transform")
    if state.basis != STF5_CARTESIAN_BASIS:
        raise OrbitNonlinearityError(
            "O(3) action requires the registered STF5 Cartesian basis"
        )
    if state.parity != DEPARTURE_O3_PARITY:
        raise OrbitNonlinearityError(
            "O(3) action requires the registered departure parity contract"
        )
    if state.frame != transform.coordinate_frame:
        raise OrbitNonlinearityError(
            "state and O(3) transform coordinate frames must match"
        )
    matrix = np.asarray(transform.matrix)
    sigma = matrix @ stf5_to_matrix(state.sigma_ab) @ matrix.T
    beta = matrix @ np.asarray(state.beta_a)
    omega = transform.determinant * matrix @ np.asarray(state.omega_a)
    return DepartureState(
        sigma_ab=matrix_to_stf5(sigma),
        omega_a=tuple(float(value) for value in omega),
        beta_a=tuple(float(value) for value in beta),
        delta_omega_k=state.delta_omega_k,
        frame=state.frame,
        congruence=state.congruence,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        basis=state.basis,
        units=state.units,
        parity=state.parity,
        perturbative_order=state.perturbative_order,
    )


@dataclass(frozen=True)
class InvariantCatalogSpec:
    """Preregistered orbit catalogue plus multiplicity/null bindings."""

    catalog_id: str
    invariant_names: tuple[str, ...]
    multiplicity_method: str
    alignment_null_id: str
    preregistration_id: str

    def __post_init__(self) -> None:
        _text(self.catalog_id, "catalog_id")
        names = _texts(self.invariant_names, "invariant_names")
        if names != PR251_INVARIANT_NAMES:
            raise OrbitNonlinearityError(
                "PR-251 catalogue names/order must match the preregistered set"
            )
        object.__setattr__(self, "invariant_names", names)
        _text(self.multiplicity_method, "multiplicity_method")
        _text(self.alignment_null_id, "alignment_null_id")
        _text(self.preregistration_id, "preregistration_id")


@dataclass(frozen=True)
class OrbitInvariantReport:
    tr_sigma2: float
    tr_sigma3: float
    beta2: float
    beta_sigma_beta: float
    beta_sigma2_beta: float
    parity_odd_det: float
    catalog_id: str
    multiplicity_method: str
    alignment_null_id: str
    preregistration_id: str
    frame: str
    congruence: str
    epoch_window: str
    averaging_scale: str
    basis: str
    units: str
    parity: str
    perturbative_order: str
    allowed_use: tuple[str, ...] = _DIAGNOSTIC_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _DIAGNOSTIC_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _ORBIT_REPORT_TOKEN:
            raise OrbitNonlinearityError(
                "OrbitInvariantReport must be created by orbit_invariants"
            )
        for name in (
            "tr_sigma2",
            "tr_sigma3",
            "beta2",
            "beta_sigma_beta",
            "beta_sigma2_beta",
            "parity_odd_det",
        ):
            object.__setattr__(self, name, _real(getattr(self, name), name))
        for name in (
            "catalog_id",
            "multiplicity_method",
            "alignment_null_id",
            "preregistration_id",
            "frame",
            "congruence",
            "epoch_window",
            "averaging_scale",
            "basis",
            "units",
            "parity",
            "perturbative_order",
        ):
            _text(getattr(self, name), name)
        allowed, forbidden = _diagnostic_lanes(
            self.allowed_use, self.forbidden_use
        )
        object.__setattr__(self, "allowed_use", allowed)
        object.__setattr__(self, "forbidden_use", forbidden)

    @property
    def even_values(self) -> tuple[float, ...]:
        return (
            self.tr_sigma2,
            self.tr_sigma3,
            self.beta2,
            self.beta_sigma_beta,
            self.beta_sigma2_beta,
        )


def orbit_invariants(
    state: DepartureState,
    catalog: InvariantCatalogSpec,
) -> OrbitInvariantReport:
    if not isinstance(state, DepartureState):
        raise TypeError("state must be a DepartureState")
    if not isinstance(catalog, InvariantCatalogSpec):
        raise TypeError("catalog must be an InvariantCatalogSpec")
    if state.basis != STF5_CARTESIAN_BASIS:
        raise OrbitNonlinearityError(
            "orbit invariants require the registered STF5 Cartesian basis"
        )
    if state.units != DEPARTURE_O3_UNITS:
        raise OrbitNonlinearityError(
            "orbit invariants require the registered dimensionless units"
        )
    if state.parity != DEPARTURE_O3_PARITY:
        raise OrbitNonlinearityError(
            "orbit invariants require the registered STF/axial/polar parity"
        )
    sigma = stf5_to_matrix(state.sigma_ab)
    sigma2 = sigma @ sigma
    beta = np.asarray(state.beta_a)
    sigma_beta = sigma @ beta
    sigma2_beta = sigma2 @ beta
    return OrbitInvariantReport(
        tr_sigma2=float(np.trace(sigma2)),
        tr_sigma3=float(np.trace(sigma2 @ sigma)),
        beta2=float(beta @ beta),
        beta_sigma_beta=float(beta @ sigma_beta),
        beta_sigma2_beta=float(beta @ sigma2_beta),
        parity_odd_det=float(
            np.linalg.det(np.column_stack((beta, sigma_beta, sigma2_beta)))
        ),
        catalog_id=catalog.catalog_id,
        multiplicity_method=catalog.multiplicity_method,
        alignment_null_id=catalog.alignment_null_id,
        preregistration_id=catalog.preregistration_id,
        frame=state.frame,
        congruence=state.congruence,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        basis=state.basis,
        units=state.units,
        parity=state.parity,
        perturbative_order=state.perturbative_order,
        _construction_token=_ORBIT_REPORT_TOKEN,
    )


@dataclass(frozen=True)
class ResponseRankReport:
    status: ResponseRankStatus
    rank: int | None
    parameter_dimension: int | None
    data_dimension: int | None
    supported_data_dimension: int | None
    singular_values: tuple[float, ...]
    min_singular: float | None
    nullspace: tuple[tuple[float, ...], ...]
    tolerance: float | None
    transfer_id: str | None
    mask_id: str | None
    covariance_id: str | None
    response_id: str | None
    covariance_content_id: str | None
    missing_inputs: tuple[str, ...]
    allowed_use: tuple[str, ...] = _DIAGNOSTIC_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _DIAGNOSTIC_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RANK_REPORT_TOKEN:
            raise OrbitNonlinearityError(
                "ResponseRankReport must be created by measure_response_rank"
            )
        if not isinstance(self.status, ResponseRankStatus):
            raise OrbitNonlinearityError(
                "status must be a ResponseRankStatus"
            )
        allowed, forbidden = _diagnostic_lanes(
            self.allowed_use, self.forbidden_use
        )
        object.__setattr__(self, "allowed_use", allowed)
        object.__setattr__(self, "forbidden_use", forbidden)
        if self.status is ResponseRankStatus.MISSING_INPUT:
            missing = _texts(self.missing_inputs, "missing_inputs")
            object.__setattr__(self, "missing_inputs", missing)
            for name in ("transfer_id", "mask_id", "covariance_id"):
                value = getattr(self, name)
                if value is not None:
                    _evidence_receipt(value, name)
            if self.response_id is not None or self.covariance_content_id is not None:
                raise OrbitNonlinearityError(
                    "MISSING_INPUT rank report must not carry array identities"
                )
            numeric = (
                self.rank,
                self.parameter_dimension,
                self.data_dimension,
                self.supported_data_dimension,
                self.min_singular,
                self.tolerance,
            )
            if any(value is not None for value in numeric):
                raise OrbitNonlinearityError(
                    "MISSING_INPUT rank report must not carry numeric claims"
                )
            if self.singular_values or self.nullspace:
                raise OrbitNonlinearityError(
                    "MISSING_INPUT rank report must not carry decompositions"
                )
            return

        if self.missing_inputs:
            raise OrbitNonlinearityError(
                "MEASURED rank report cannot carry missing_inputs"
            )
        for name in (
            "rank",
            "parameter_dimension",
            "data_dimension",
            "supported_data_dimension",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise OrbitNonlinearityError(
                    f"{name} must be a non-negative integer"
                )
        if self.parameter_dimension == 0 or self.data_dimension == 0:
            raise OrbitNonlinearityError(
                "MEASURED rank report requires positive matrix dimensions"
            )
        if self.rank > min(
            self.parameter_dimension, self.supported_data_dimension
        ):
            raise OrbitNonlinearityError("rank exceeds a matrix dimension")
        if self.supported_data_dimension > self.data_dimension:
            raise OrbitNonlinearityError(
                "supported_data_dimension exceeds data_dimension"
            )
        singular = tuple(
            _nonnegative(value, "singular_values")
            for value in self.singular_values
        )
        if any(
            left < right
            for left, right in zip(singular, singular[1:])
        ):
            raise OrbitNonlinearityError(
                "singular_values must be descending"
            )
        expected_singular_count = min(
            self.supported_data_dimension, self.parameter_dimension
        )
        if len(singular) != expected_singular_count:
            raise OrbitNonlinearityError(
                "singular_values count must match the supported matrix shape"
            )
        object.__setattr__(self, "singular_values", singular)
        tolerance = _nonnegative(self.tolerance, "tolerance")
        expected_rank = sum(value > tolerance for value in singular)
        if self.rank != expected_rank:
            raise OrbitNonlinearityError(
                "rank must be derived from singular_values and tolerance"
            )
        expected_min = (
            0.0
            if self.rank < self.parameter_dimension
            else (singular[-1] if singular else 0.0)
        )
        if not math.isclose(
            _nonnegative(self.min_singular, "min_singular"),
            expected_min,
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            raise OrbitNonlinearityError(
                "min_singular must expose structural parameter nulls as zero"
        )
        object.__setattr__(self, "min_singular", expected_min)
        object.__setattr__(self, "tolerance", tolerance)
        for name in ("transfer_id", "mask_id", "covariance_id"):
            _evidence_receipt(getattr(self, name), name)
        for name in ("response_id", "covariance_content_id"):
            _evidence_receipt(getattr(self, name), name)
        nullspace = tuple(
            tuple(
                float(value)
                for value in _array(
                    row,
                    "nullspace",
                    shape=(self.parameter_dimension,),
                )
            )
            for row in self.nullspace
        )
        if len(nullspace) != self.parameter_dimension - self.rank:
            raise OrbitNonlinearityError(
                "nullspace dimension must equal parameter_dimension-rank"
            )
        object.__setattr__(self, "nullspace", nullspace)

    @property
    def identifiable(self) -> bool:
        return (
            self.status is ResponseRankStatus.MEASURED
            and self.rank == self.parameter_dimension
        )


def _covariance_support(
    covariance: object,
    *,
    rtol: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    rtol = _relative_tolerance(rtol)
    value = _array(covariance, "covariance", ndim=2)
    if value.shape[0] != value.shape[1]:
        raise OrbitNonlinearityError("covariance must be square")
    if value.shape[0] == 0:
        raise OrbitNonlinearityError("covariance must not be empty")
    scale = float(np.max(np.abs(value), initial=0.0))
    symmetry_tolerance = 64.0 * np.finfo(float).eps * scale
    if not np.allclose(value, value.T, atol=symmetry_tolerance, rtol=0.0):
        raise OrbitNonlinearityError("covariance must be symmetric")
    eigenvalues, eigenvectors = np.linalg.eigh(value)
    spectral_scale = (
        float(np.max(np.abs(eigenvalues))) if eigenvalues.size else 0.0
    )
    psd_tolerance = 64.0 * np.finfo(float).eps * spectral_scale
    if float(np.min(eigenvalues, initial=0.0)) < -psd_tolerance:
        raise OrbitNonlinearityError(
            "covariance must be positive semidefinite"
        )
    tolerance = rtol * spectral_scale
    support = eigenvalues > tolerance
    return eigenvalues, eigenvectors, support, tolerance


def _whiten_supported(
    value: np.ndarray,
    covariance: object,
    *,
    rtol: float,
    scale_invariant: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    eigenvalues, eigenvectors, support, tolerance = _covariance_support(
        covariance, rtol=rtol
    )
    if value.shape[0] != eigenvectors.shape[0]:
        raise OrbitNonlinearityError(
            "response/residual and covariance row counts must agree"
        )
    supported = eigenvectors[:, support]
    if supported.shape[1] == 0:
        whitened = np.empty((0, *value.shape[1:]), dtype=float)
    else:
        projected_value = value
        if scale_invariant:
            value_scale = float(np.max(np.abs(value), initial=0.0))
            if value_scale > 0.0:
                projected_value = value / value_scale
        projected = supported.T @ projected_value
        scale = np.sqrt(eigenvalues[support])
        if scale_invariant:
            # A positive common covariance scale cannot change a response
            # rank or tangent subspace.  Remove it before division so finite
            # response/covariance pairs cannot silently underflow to rank 0.
            scale = scale / float(np.max(scale))
        if value.ndim == 1:
            whitened = projected / scale
        else:
            whitened = projected / scale[:, None]
        if not np.isfinite(whitened).all():
            raise OrbitNonlinearityError(
                "supported whitening is not representable at float64 precision"
            )
    null_vectors = eigenvectors[:, ~support]
    return whitened, null_vectors, supported, tolerance


def _svd_rank(
    matrix: np.ndarray,
    *,
    rtol: float,
) -> tuple[int, np.ndarray, float, np.ndarray]:
    _, singular, vt = np.linalg.svd(matrix, full_matrices=True)
    scale = float(singular[0]) if singular.size else 0.0
    tolerance = rtol * scale
    rank = int(np.count_nonzero(singular > tolerance))
    nullspace = vt[rank:, :] if vt.shape[0] > rank else np.empty(
        (0, matrix.shape[1])
    )
    return rank, singular, tolerance, nullspace


def measure_response_rank(
    *,
    response: object | None,
    covariance: object | None,
    transfer_id: str | None,
    mask_id: str | None,
    covariance_id: str | None,
    rtol: float = 1e-12,
) -> ResponseRankReport:
    """Measure rank only from a supplied, identity-bound response."""

    missing = tuple(
        name
        for name, value in (
            ("response", response),
            ("covariance", covariance),
            ("transfer_id", transfer_id),
            ("mask_id", mask_id),
            ("covariance_id", covariance_id),
        )
        if value is None
    )
    if missing:
        return ResponseRankReport(
            status=ResponseRankStatus.MISSING_INPUT,
            rank=None,
            parameter_dimension=None,
            data_dimension=None,
            supported_data_dimension=None,
            singular_values=(),
            min_singular=None,
            nullspace=(),
            tolerance=None,
            transfer_id=transfer_id,
            mask_id=mask_id,
            covariance_id=covariance_id,
            response_id=None,
            covariance_content_id=None,
            missing_inputs=missing,
            _construction_token=_RANK_REPORT_TOKEN,
        )
    rtol = _relative_tolerance(rtol)
    matrix = _array(response, "response", ndim=2)
    if matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise OrbitNonlinearityError(
            "response must have positive data and parameter dimensions"
        )
    for name, value in (
        ("transfer_id", transfer_id),
        ("mask_id", mask_id),
        ("covariance_id", covariance_id),
    ):
        _evidence_receipt(value, name)
    covariance_matrix = _array(covariance, "covariance", ndim=2)
    whitened, _, supported, _ = _whiten_supported(
        matrix,
        covariance_matrix,
        rtol=rtol,
        scale_invariant=True,
    )
    rank, singular, tolerance, nullspace = _svd_rank(
        whitened, rtol=rtol
    )
    minimum = (
        0.0
        if rank < matrix.shape[1]
        else (float(singular[-1]) if singular.size else 0.0)
    )
    return ResponseRankReport(
        status=ResponseRankStatus.MEASURED,
        rank=rank,
        parameter_dimension=matrix.shape[1],
        data_dimension=matrix.shape[0],
        supported_data_dimension=supported.shape[1],
        singular_values=tuple(float(value) for value in singular),
        min_singular=minimum,
        nullspace=tuple(
            tuple(float(value) for value in row) for row in nullspace
        ),
        tolerance=float(tolerance),
        transfer_id=transfer_id,
        mask_id=mask_id,
        covariance_id=covariance_id,
        response_id=_array_content_identity(matrix),
        covariance_content_id=_array_content_identity(covariance_matrix),
        missing_inputs=(),
        _construction_token=_RANK_REPORT_TOKEN,
    )


@dataclass(frozen=True)
class CandidateIndependenceReceipt:
    """Declared train/fit/split boundary bound to exact evaluation targets."""

    candidate_id: str
    model_config_id: str
    training_data_id: str
    held_out_data_id: str
    matched_injection_data_id: str
    fit_receipt_id: str
    split_receipt_id: str
    receipt_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CANDIDATE_INDEPENDENCE_TOKEN:
            raise OrbitNonlinearityError(
                "CandidateIndependenceReceipt must be created by "
                "build_candidate_independence_receipt"
            )
        _text(self.candidate_id, "candidate_id")
        for name in (
            "model_config_id",
            "training_data_id",
            "held_out_data_id",
            "matched_injection_data_id",
            "fit_receipt_id",
            "split_receipt_id",
            "receipt_id",
        ):
            object.__setattr__(
                self, name, _evidence_receipt(getattr(self, name), name)
            )
        data_ids = {
            self.training_data_id,
            self.held_out_data_id,
            self.matched_injection_data_id,
        }
        if len(data_ids) != 3:
            raise OrbitNonlinearityError(
                "training, held-out and matched-injection data identities "
                "must be distinct"
            )
        boundary_ids = {
            self.model_config_id,
            self.fit_receipt_id,
            self.split_receipt_id,
            *data_ids,
        }
        if len(boundary_ids) != 6:
            raise OrbitNonlinearityError(
                "model, fit and split receipts must be distinct from each "
                "other and from all data identities"
            )
        expected_id = _candidate_independence_identity(
            candidate_id=self.candidate_id,
            model_config_id=self.model_config_id,
            training_data_id=self.training_data_id,
            held_out_data_id=self.held_out_data_id,
            matched_injection_data_id=self.matched_injection_data_id,
            fit_receipt_id=self.fit_receipt_id,
            split_receipt_id=self.split_receipt_id,
        )
        if self.receipt_id != expected_id:
            raise OrbitNonlinearityError(
                "receipt_id does not bind the candidate independence boundary"
            )


def _candidate_independence_identity(
    *,
    candidate_id: str,
    model_config_id: str,
    training_data_id: str,
    held_out_data_id: str,
    matched_injection_data_id: str,
    fit_receipt_id: str,
    split_receipt_id: str,
) -> str:
    payload = {
        "candidate_id": candidate_id,
        "fit_receipt_id": fit_receipt_id,
        "held_out_data_id": held_out_data_id,
        "matched_injection_data_id": matched_injection_data_id,
        "model_config_id": model_config_id,
        "schema": "CANDIDATE_INDEPENDENCE_RECEIPT_V1",
        "split_receipt_id": split_receipt_id,
        "training_data_id": training_data_id,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def build_candidate_independence_receipt(
    *,
    candidate_id: str,
    model_config_id: str,
    training_data_id: str,
    held_out_target: object,
    matched_injection_target: object,
    fit_receipt_id: str,
    split_receipt_id: str,
) -> CandidateIndependenceReceipt:
    """Bind a declared independent fit/split to exact evaluation targets.

    This receipt records a fail-closed evidence boundary; it is not a
    platform-authenticated proof that the declared training process occurred.
    """

    candidate = _text(candidate_id, "candidate_id")
    model = _evidence_receipt(model_config_id, "model_config_id")
    training = _evidence_receipt(training_data_id, "training_data_id")
    fit = _evidence_receipt(fit_receipt_id, "fit_receipt_id")
    split = _evidence_receipt(split_receipt_id, "split_receipt_id")
    held_target = _array(held_out_target, "held_out_target", ndim=1)
    injection_target = _array(
        matched_injection_target, "matched_injection_target", ndim=1
    )
    if held_target.size == 0 or injection_target.size == 0:
        raise OrbitNonlinearityError(
            "independence receipt targets must be non-empty"
        )
    held_data_id = _array_content_identity(held_target)
    injection_data_id = _array_content_identity(injection_target)
    receipt_id = _candidate_independence_identity(
        candidate_id=candidate,
        model_config_id=model,
        training_data_id=training,
        held_out_data_id=held_data_id,
        matched_injection_data_id=injection_data_id,
        fit_receipt_id=fit,
        split_receipt_id=split,
    )
    return CandidateIndependenceReceipt(
        candidate_id=candidate,
        model_config_id=model,
        training_data_id=training,
        held_out_data_id=held_data_id,
        matched_injection_data_id=injection_data_id,
        fit_receipt_id=fit,
        split_receipt_id=split,
        receipt_id=receipt_id,
        _construction_token=_CANDIDATE_INDEPENDENCE_TOKEN,
    )


@dataclass(frozen=True)
class CandidateEvaluation:
    """Factory-derived held-out scores bound to predictions and fit evidence."""

    candidate_id: str
    kind: CandidateKind
    held_out_score: float
    matched_injection_score: float
    held_out_data_id: str
    matched_injection_data_id: str
    model_config_id: str
    scoring_rule: CandidateScoringRule
    held_out_prediction_id: str
    matched_injection_prediction_id: str
    independence_receipt: CandidateIndependenceReceipt
    evaluation_id: str
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CANDIDATE_EVALUATION_TOKEN:
            raise OrbitNonlinearityError(
                "CandidateEvaluation must be created by "
                "evaluate_candidate_predictions"
            )
        _text(self.candidate_id, "candidate_id")
        if not isinstance(self.kind, CandidateKind):
            raise OrbitNonlinearityError("kind must be a CandidateKind")
        if not isinstance(self.scoring_rule, CandidateScoringRule):
            raise OrbitNonlinearityError(
                "scoring_rule must be a CandidateScoringRule"
            )
        object.__setattr__(
            self, "held_out_score", _real(self.held_out_score, "held_out_score")
        )
        object.__setattr__(
            self,
            "matched_injection_score",
            _real(self.matched_injection_score, "matched_injection_score"),
        )
        object.__setattr__(
            self,
            "held_out_data_id",
            _evidence_receipt(self.held_out_data_id, "held_out_data_id"),
        )
        object.__setattr__(
            self,
            "matched_injection_data_id",
            _evidence_receipt(
                self.matched_injection_data_id,
                "matched_injection_data_id",
            ),
        )
        for name in (
            "model_config_id",
            "held_out_prediction_id",
            "matched_injection_prediction_id",
            "evaluation_id",
        ):
            object.__setattr__(
                self, name, _evidence_receipt(getattr(self, name), name)
            )
        if type(self.independence_receipt) is not CandidateIndependenceReceipt:
            raise OrbitNonlinearityError(
                "independence_receipt must be a "
                "CandidateIndependenceReceipt"
            )
        if (
            self.independence_receipt.candidate_id != self.candidate_id
            or self.independence_receipt.model_config_id
            != self.model_config_id
            or self.independence_receipt.held_out_data_id
            != self.held_out_data_id
            or self.independence_receipt.matched_injection_data_id
            != self.matched_injection_data_id
        ):
            raise OrbitNonlinearityError(
                "independence receipt does not match the candidate, model "
                "and evaluation targets"
            )
        if self.held_out_data_id == self.matched_injection_data_id:
            raise OrbitNonlinearityError(
                "held-out and matched-injection data identities must differ"
            )
        expected_id = _candidate_evaluation_identity(
            candidate_id=self.candidate_id,
            kind=self.kind,
            held_out_score=self.held_out_score,
            matched_injection_score=self.matched_injection_score,
            held_out_data_id=self.held_out_data_id,
            matched_injection_data_id=self.matched_injection_data_id,
            model_config_id=self.model_config_id,
            scoring_rule=self.scoring_rule,
            held_out_prediction_id=self.held_out_prediction_id,
            matched_injection_prediction_id=(
                self.matched_injection_prediction_id
            ),
            independence_receipt_id=self.independence_receipt.receipt_id,
        )
        if self.evaluation_id != expected_id:
            raise OrbitNonlinearityError(
                "evaluation_id does not bind the candidate evaluation"
            )


def _negative_mean_squared_error(
    prediction: np.ndarray,
    target: np.ndarray,
    *,
    name: str,
) -> float:
    difference = prediction - target
    if not np.isfinite(difference).all():
        raise OrbitNonlinearityError(
            f"{name} prediction-target difference is not finite"
        )
    scale = float(np.max(np.abs(difference), initial=0.0))
    if scale == 0.0:
        return -0.0
    normalized = difference / scale
    mean_square = float(np.mean(normalized * normalized))
    if mean_square > 0.0 and scale > (
        math.sqrt(np.finfo(float).max) / math.sqrt(mean_square)
    ):
        raise OrbitNonlinearityError(f"{name} score is not finite")
    score = -(scale * scale) * mean_square
    if not math.isfinite(score):
        raise OrbitNonlinearityError(f"{name} score is not finite")
    return score


def _candidate_evaluation_identity(
    *,
    candidate_id: str,
    kind: CandidateKind,
    held_out_score: float,
    matched_injection_score: float,
    held_out_data_id: str,
    matched_injection_data_id: str,
    model_config_id: str,
    scoring_rule: CandidateScoringRule,
    held_out_prediction_id: str,
    matched_injection_prediction_id: str,
    independence_receipt_id: str,
) -> str:
    payload = {
        "candidate_id": candidate_id,
        "held_out_data_id": held_out_data_id,
        "held_out_prediction_id": held_out_prediction_id,
        "held_out_score_hex": held_out_score.hex(),
        "independence_receipt_id": independence_receipt_id,
        "kind": kind.value,
        "matched_injection_data_id": matched_injection_data_id,
        "matched_injection_prediction_id": matched_injection_prediction_id,
        "matched_injection_score_hex": matched_injection_score.hex(),
        "model_config_id": model_config_id,
        "schema": "CANDIDATE_EVALUATION_V2",
        "scoring_rule": scoring_rule.value,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def evaluate_candidate_predictions(
    *,
    candidate_id: str,
    kind: CandidateKind,
    held_out_prediction: object,
    held_out_target: object,
    matched_injection_prediction: object,
    matched_injection_target: object,
    model_config_id: str,
    independence_receipt: CandidateIndependenceReceipt,
    scoring_rule: CandidateScoringRule = (
        CandidateScoringRule.NEGATIVE_MEAN_SQUARED_ERROR
    ),
) -> CandidateEvaluation:
    """Compute and bind one candidate evaluation from exact numeric arrays."""

    _text(candidate_id, "candidate_id")
    if not isinstance(kind, CandidateKind):
        raise OrbitNonlinearityError("kind must be a CandidateKind")
    if not isinstance(scoring_rule, CandidateScoringRule):
        raise OrbitNonlinearityError(
            "scoring_rule must be a CandidateScoringRule"
        )
    model_id = _evidence_receipt(model_config_id, "model_config_id")
    if type(independence_receipt) is not CandidateIndependenceReceipt:
        raise OrbitNonlinearityError(
            "independence_receipt must be a CandidateIndependenceReceipt"
        )
    held_prediction = _array(
        held_out_prediction, "held_out_prediction", ndim=1
    )
    held_target = _array(held_out_target, "held_out_target", ndim=1)
    injection_prediction = _array(
        matched_injection_prediction,
        "matched_injection_prediction",
        ndim=1,
    )
    injection_target = _array(
        matched_injection_target, "matched_injection_target", ndim=1
    )
    for name, prediction, target in (
        ("held_out", held_prediction, held_target),
        ("matched_injection", injection_prediction, injection_target),
    ):
        if prediction.size == 0 or prediction.shape != target.shape:
            raise OrbitNonlinearityError(
                f"{name} prediction and target must have the same non-empty shape"
            )
    held_score = _negative_mean_squared_error(
        held_prediction, held_target, name="held_out"
    )
    injection_score = _negative_mean_squared_error(
        injection_prediction, injection_target, name="matched_injection"
    )
    held_data_id = _array_content_identity(held_target)
    injection_data_id = _array_content_identity(injection_target)
    held_prediction_id = _array_content_identity(held_prediction)
    injection_prediction_id = _array_content_identity(injection_prediction)
    if (
        held_prediction_id == held_data_id
        or injection_prediction_id == injection_data_id
    ):
        raise OrbitNonlinearityError(
            "prediction bytes must not equal evaluation-target bytes; "
            "target-copy independence is unverifiable"
        )
    if (
        independence_receipt.candidate_id != candidate_id
        or independence_receipt.model_config_id != model_id
        or independence_receipt.held_out_data_id != held_data_id
        or independence_receipt.matched_injection_data_id
        != injection_data_id
    ):
        raise OrbitNonlinearityError(
            "independence_receipt does not bind this candidate, model and "
            "evaluation targets"
        )
    evaluation_id = _candidate_evaluation_identity(
        candidate_id=candidate_id,
        kind=kind,
        held_out_score=held_score,
        matched_injection_score=injection_score,
        held_out_data_id=held_data_id,
        matched_injection_data_id=injection_data_id,
        model_config_id=model_id,
        scoring_rule=scoring_rule,
        held_out_prediction_id=held_prediction_id,
        matched_injection_prediction_id=injection_prediction_id,
        independence_receipt_id=independence_receipt.receipt_id,
    )
    return CandidateEvaluation(
        candidate_id=candidate_id,
        kind=kind,
        held_out_score=held_score,
        matched_injection_score=injection_score,
        held_out_data_id=held_data_id,
        matched_injection_data_id=injection_data_id,
        model_config_id=model_id,
        scoring_rule=scoring_rule,
        held_out_prediction_id=held_prediction_id,
        matched_injection_prediction_id=injection_prediction_id,
        independence_receipt=independence_receipt,
        evaluation_id=evaluation_id,
        _construction_token=_CANDIDATE_EVALUATION_TOKEN,
    )


def _select_nonlinear_winner(
    nonlinear: Sequence[CandidateEvaluation],
    controls: Sequence[CandidateEvaluation],
    *,
    gain_margin: float,
) -> CandidateEvaluation | None:
    """Select only among candidates that clear both registered score axes.

    Ranking by one axis before applying the other can discard a candidate that
    is the only member to beat every control on both held-out and matched-
    injection data.  The tie-break below maximizes the weaker excess margin
    first, then the two score axes, and finally the unique candidate id so the
    result is independent of caller ordering.
    """

    if not nonlinear or not controls:
        return None
    held_threshold = (
        max(value.held_out_score for value in controls) + gain_margin
    )
    injection_threshold = (
        max(value.matched_injection_score for value in controls)
        + gain_margin
    )
    eligible = tuple(
        value
        for value in nonlinear
        if value.held_out_score >= held_threshold
        and value.matched_injection_score >= injection_threshold
    )
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda value: (
            min(
                value.held_out_score - held_threshold,
                value.matched_injection_score - injection_threshold,
            ),
            value.held_out_score,
            value.matched_injection_score,
            value.candidate_id,
        ),
    )


@dataclass(frozen=True)
class NonlinearityReport:
    tangent_statistic: float | None
    perpendicular_statistic: float | None
    delta_nl: float | None
    null_residual_sq: float | None
    response_rank: ResponseRankReport
    candidate_comparisons: tuple[CandidateEvaluation, ...]
    held_out_receipt: str | None
    matched_injection_receipt: str | None
    off_manifold_tolerance: float | None
    null_residual_tolerance: float | None
    nonlinear_gain_margin: float | None
    attribution_status: NonlinearityAttributionStatus
    attribution_rationale: str
    found_equiv_status: str = FOUND_EQUIV_STATUS
    found_equiv_prerequisite: str = FOUND_EQUIV_PREREQUISITE
    allowed_use: tuple[str, ...] = _DIAGNOSTIC_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _DIAGNOSTIC_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _NONLINEARITY_REPORT_TOKEN:
            raise OrbitNonlinearityError(
                "NonlinearityReport must be created by decompose_nonlinearity"
            )
        if not isinstance(self.response_rank, ResponseRankReport):
            raise OrbitNonlinearityError(
                "response_rank must be a ResponseRankReport"
            )
        if not isinstance(
            self.attribution_status, NonlinearityAttributionStatus
        ):
            raise OrbitNonlinearityError(
                "attribution_status must be a NonlinearityAttributionStatus"
            )
        if self.attribution_status is NonlinearityAttributionStatus.MISSING_RESPONSE:
            if self.response_rank.status is not ResponseRankStatus.MISSING_INPUT:
                raise OrbitNonlinearityError(
                    "MISSING_RESPONSE requires a missing-input rank report"
                )
            if any(
                value is not None
                for value in (
                    self.tangent_statistic,
                    self.perpendicular_statistic,
                    self.delta_nl,
                    self.null_residual_sq,
                    self.off_manifold_tolerance,
                    self.null_residual_tolerance,
                    self.nonlinear_gain_margin,
                )
            ):
                raise OrbitNonlinearityError(
                    "MISSING_RESPONSE report cannot carry statistics"
                )
        else:
            if self.response_rank.status is not ResponseRankStatus.MEASURED:
                raise OrbitNonlinearityError(
                    "non-missing attribution requires a measured rank report"
                )
            object.__setattr__(
                self,
                "tangent_statistic",
                _nonnegative(self.tangent_statistic, "tangent_statistic"),
            )
            object.__setattr__(
                self,
                "perpendicular_statistic",
                _nonnegative(
                    self.perpendicular_statistic, "perpendicular_statistic"
                ),
            )
            object.__setattr__(
                self,
                "null_residual_sq",
                _nonnegative(self.null_residual_sq, "null_residual_sq"),
            )
            if self.delta_nl is not None:
                object.__setattr__(
                    self, "delta_nl", _nonnegative(self.delta_nl, "delta_nl")
                )
            object.__setattr__(
                self,
                "off_manifold_tolerance",
                _nonnegative(
                    self.off_manifold_tolerance, "off_manifold_tolerance"
                ),
            )
            object.__setattr__(
                self,
                "null_residual_tolerance",
                _nonnegative(
                    self.null_residual_tolerance, "null_residual_tolerance"
                ),
            )
            object.__setattr__(
                self,
                "nonlinear_gain_margin",
                _positive(
                    self.nonlinear_gain_margin, "nonlinear_gain_margin"
                ),
            )
        comparisons = tuple(self.candidate_comparisons)
        if any(
            not isinstance(value, CandidateEvaluation)
            for value in comparisons
        ):
            raise OrbitNonlinearityError(
                "candidate_comparisons must contain CandidateEvaluation values"
            )
        if len({value.candidate_id for value in comparisons}) != len(comparisons):
            raise OrbitNonlinearityError("candidate ids must be unique")
        if comparisons and len(
            {
                value.independence_receipt.split_receipt_id
                for value in comparisons
            }
        ) != 1:
            raise OrbitNonlinearityError(
                "candidate comparisons must share one held-out split receipt"
            )
        if len(
            {
                value.independence_receipt.fit_receipt_id
                for value in comparisons
            }
        ) != len(comparisons):
            raise OrbitNonlinearityError(
                "candidate comparisons require unique fit receipts"
            )
        object.__setattr__(self, "candidate_comparisons", comparisons)
        if (
            self.attribution_status
            is NonlinearityAttributionStatus.MISSING_RESPONSE
            and (
                comparisons
                or self.held_out_receipt is not None
                or self.matched_injection_receipt is not None
            )
        ):
            raise OrbitNonlinearityError(
                "MISSING_RESPONSE report cannot carry candidate evidence"
            )
        if self.held_out_receipt is not None:
            object.__setattr__(
                self,
                "held_out_receipt",
                _evidence_receipt(
                    self.held_out_receipt, "held_out_receipt"
                ),
            )
        if self.matched_injection_receipt is not None:
            object.__setattr__(
                self,
                "matched_injection_receipt",
                _evidence_receipt(
                    self.matched_injection_receipt,
                    "matched_injection_receipt",
                ),
            )
        if (
            self.held_out_receipt is not None
            and self.held_out_receipt == self.matched_injection_receipt
        ):
            raise OrbitNonlinearityError(
                "held-out and matched-injection receipts must differ"
            )
        if (
            self.attribution_status
            is NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
            and (
                self.held_out_receipt is None
                or self.matched_injection_receipt is None
            )
        ):
            raise OrbitNonlinearityError(
                "NONLINEAR_COMPATIBLE requires held-out and "
                "matched-injection receipts"
            )
        if self.attribution_status is not NonlinearityAttributionStatus.MISSING_RESPONSE:
            null_outside = (
                self.null_residual_sq > self.null_residual_tolerance
            )
            off_manifold = (
                self.perpendicular_statistic > self.off_manifold_tolerance
            )
            kinds = {value.kind for value in comparisons}
            nonlinear = tuple(
                value
                for value in comparisons
                if value.kind is CandidateKind.NONLINEAR
            )
            complete = (
                self.held_out_receipt is not None
                and self.matched_injection_receipt is not None
                and bool(nonlinear)
                and _REQUIRED_ALTERNATIVES.issubset(kinds)
                and all(
                    (
                        value.held_out_data_id == self.held_out_receipt
                        and value.matched_injection_data_id
                        == self.matched_injection_receipt
                    )
                    for value in comparisons
                )
            )
            nonlinear_wins = False
            if complete:
                controls = tuple(
                    value
                    for value in comparisons
                    if value.kind is not CandidateKind.NONLINEAR
                )
                winner = _select_nonlinear_winner(
                    nonlinear,
                    controls,
                    gain_margin=self.nonlinear_gain_margin,
                )
                nonlinear_wins = winner is not None
            expected = (
                NonlinearityAttributionStatus.NON_IDENTIFIED_RESPONSE
                if not self.response_rank.identifiable
                else (
                    NonlinearityAttributionStatus.OUTSIDE_SUPPORTED_QUOTIENT
                    if null_outside
                    else (
                        NonlinearityAttributionStatus.LINEAR_COMPATIBLE
                        if not off_manifold
                        else (
                            NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
                            if nonlinear_wins
                            else NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
                        )
                    )
                )
            )
            if self.attribution_status is not expected:
                raise OrbitNonlinearityError(
                    "attribution_status does not follow the sealed statistics "
                    "and held-out competition"
                )
        _text(self.attribution_rationale, "attribution_rationale")
        if self.found_equiv_status != FOUND_EQUIV_STATUS:
            raise OrbitNonlinearityError(
                "FOUND-EQUIV must remain ACTIVE_CONDITIONAL"
            )
        if self.found_equiv_prerequisite != FOUND_EQUIV_PREREQUISITE:
            raise OrbitNonlinearityError(
                "FOUND-EQUIV must remain conditional on EGS3-B1"
            )
        allowed, forbidden = _diagnostic_lanes(
            self.allowed_use, self.forbidden_use
        )
        object.__setattr__(self, "allowed_use", allowed)
        object.__setattr__(self, "forbidden_use", forbidden)


def decompose_nonlinearity(
    *,
    residual: object,
    tangent_response: object | None,
    covariance: object | None,
    transfer_id: str | None,
    mask_id: str | None,
    covariance_id: str | None,
    candidates: Sequence[CandidateEvaluation] = (),
    held_out_receipt: str | None = None,
    matched_injection_receipt: str | None = None,
    off_manifold_tolerance: float,
    null_residual_tolerance: float,
    nonlinear_gain_margin: float,
    delta_nl: float | None = None,
    rtol: float = 1e-12,
) -> NonlinearityReport:
    """Decompose a residual and gate any nonlinear attribution.

    A nonlinear label is returned only when one nonlinear candidate beats
    linear, systematics, frame-mismatch, and derivative-failure controls on
    both held-out and matched-injection scores by the declared margin.
    """

    rank_report = measure_response_rank(
        response=tangent_response,
        covariance=covariance,
        transfer_id=transfer_id,
        mask_id=mask_id,
        covariance_id=covariance_id,
        rtol=rtol,
    )
    if rank_report.status is ResponseRankStatus.MISSING_INPUT:
        return NonlinearityReport(
            tangent_statistic=None,
            perpendicular_statistic=None,
            delta_nl=None,
            null_residual_sq=None,
            response_rank=rank_report,
            candidate_comparisons=(),
            held_out_receipt=None,
            matched_injection_receipt=None,
            off_manifold_tolerance=None,
            null_residual_tolerance=None,
            nonlinear_gain_margin=None,
            attribution_status=NonlinearityAttributionStatus.MISSING_RESPONSE,
            attribution_rationale=(
                "transfer, mask, covariance and tangent response are required"
            ),
            _construction_token=_NONLINEARITY_REPORT_TOKEN,
        )
    off_tolerance = _nonnegative(
        off_manifold_tolerance, "off_manifold_tolerance"
    )
    null_tolerance = _nonnegative(
        null_residual_tolerance, "null_residual_tolerance"
    )
    gain_margin = _positive(nonlinear_gain_margin, "nonlinear_gain_margin")
    rtol = _relative_tolerance(rtol)
    residual_vector = _array(residual, "residual", ndim=1)
    response = _array(tangent_response, "tangent_response", ndim=2)
    if residual_vector.shape[0] != response.shape[0]:
        raise OrbitNonlinearityError(
            "residual and tangent_response row counts must agree"
        )
    whitened_residual, null_vectors, _, _ = _whiten_supported(
        residual_vector, covariance, rtol=rtol
    )
    whitened_response, _, _, _ = _whiten_supported(
        response,
        covariance,
        rtol=rtol,
        scale_invariant=True,
    )
    if rank_report.rank:
        u, _, _ = np.linalg.svd(whitened_response, full_matrices=False)
        tangent_basis = u[:, : rank_report.rank]
        tangent = tangent_basis @ (tangent_basis.T @ whitened_residual)
    else:
        tangent = np.zeros_like(whitened_residual)
    perpendicular = whitened_residual - tangent
    tangent_statistic = float(tangent @ tangent)
    perpendicular_statistic = float(perpendicular @ perpendicular)
    null_component = null_vectors.T @ residual_vector
    null_residual_sq = float(null_component @ null_component)
    delta_value = (
        None if delta_nl is None else _nonnegative(delta_nl, "delta_nl")
    )

    comparisons = tuple(candidates)
    if any(
        not isinstance(value, CandidateEvaluation) for value in comparisons
    ):
        raise OrbitNonlinearityError(
            "candidates must contain CandidateEvaluation values"
        )
    if len({value.candidate_id for value in comparisons}) != len(comparisons):
        raise OrbitNonlinearityError("candidate ids must be unique")

    if not rank_report.identifiable:
        status = NonlinearityAttributionStatus.NON_IDENTIFIED_RESPONSE
        rationale = (
            "response rank is below the registered parameter dimension"
        )
    elif null_residual_sq > null_tolerance:
        status = NonlinearityAttributionStatus.OUTSIDE_SUPPORTED_QUOTIENT
        rationale = (
            "residual has a component in the covariance-null subspace"
        )
    elif perpendicular_statistic <= off_tolerance:
        status = NonlinearityAttributionStatus.LINEAR_COMPATIBLE
        rationale = "perpendicular statistic is within the registered tolerance"
    else:
        kinds = {value.kind for value in comparisons}
        nonlinear = tuple(
            value for value in comparisons if value.kind is CandidateKind.NONLINEAR
        )
        if (
            held_out_receipt is None
            or matched_injection_receipt is None
            or not nonlinear
            or not _REQUIRED_ALTERNATIVES.issubset(kinds)
            or any(
                (
                    value.held_out_data_id != held_out_receipt
                    or value.matched_injection_data_id
                    != matched_injection_receipt
                )
                for value in comparisons
            )
        ):
            status = NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
            rationale = (
                "off-manifold residual lacks a complete identity-bound "
                "held-out candidate competition"
            )
        else:
            controls = tuple(
                value
                for value in comparisons
                if value.kind is not CandidateKind.NONLINEAR
            )
            winner = _select_nonlinear_winner(
                nonlinear,
                controls,
                gain_margin=gain_margin,
            )
            if winner is not None:
                status = NonlinearityAttributionStatus.NONLINEAR_COMPATIBLE
                rationale = (
                    f"registered nonlinear candidate {winner.candidate_id!r} "
                    "wins held-out and matched-injection comparisons over "
                    "every alternative"
                )
            else:
                status = (
                    NonlinearityAttributionStatus.UNATTRIBUTED_OFF_MANIFOLD
                )
                rationale = (
                    "off-manifold residual is not separated from all "
                    "registered alternatives"
                )

    return NonlinearityReport(
        tangent_statistic=tangent_statistic,
        perpendicular_statistic=perpendicular_statistic,
        delta_nl=delta_value,
        null_residual_sq=null_residual_sq,
        response_rank=rank_report,
        candidate_comparisons=comparisons,
        held_out_receipt=held_out_receipt,
        matched_injection_receipt=matched_injection_receipt,
        off_manifold_tolerance=off_tolerance,
        null_residual_tolerance=null_tolerance,
        nonlinear_gain_margin=gain_margin,
        attribution_status=status,
        attribution_rationale=rationale,
        _construction_token=_NONLINEARITY_REPORT_TOKEN,
    )


__all__ = [
    "ACTIVE_O3_CONVENTION",
    "CandidateEvaluation",
    "CandidateIndependenceReceipt",
    "CandidateKind",
    "CandidateScoringRule",
    "DEPARTURE_O3_PARITY",
    "DEPARTURE_O3_UNITS",
    "FOUND_EQUIV_PREREQUISITE",
    "FOUND_EQUIV_STATUS",
    "InvariantCatalogSpec",
    "NonlinearityAttributionStatus",
    "NonlinearityReport",
    "O3Transform",
    "OrbitInvariantReport",
    "OrbitNonlinearityError",
    "OrientedDirection",
    "PR251_INVARIANT_NAMES",
    "ResponseRankReport",
    "ResponseRankStatus",
    "STF5_CARTESIAN_BASIS",
    "VectorParity",
    "build_candidate_independence_receipt",
    "decompose_nonlinearity",
    "evaluate_candidate_predictions",
    "matrix_to_stf5",
    "measure_response_rank",
    "orbit_invariants",
    "stf5_to_matrix",
    "transform_departure_state",
]

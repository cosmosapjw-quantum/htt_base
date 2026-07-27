"""Rotation-covariant low-ell pole estimates with explicit abstention.

This module is a numerical kernel.  ``gap_tolerance`` controls only whether a
one-dimensional eigenspace is numerically identifiable; it is not a substitute
for mask, noise, foreground, or sampling uncertainty.

Inputs use dense, orthonormal complex spherical-harmonic coefficients in
Condon--Shortley convention, with every ``m=-ell,...,+ell`` present and the
real-scalar-map relation ``a[l,-m]=(-1)^m conjugate(a[l,m])``.  Returned xyz
axes are expressed in the input coordinate frame.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import hashlib
import json
import math
import operator

import numpy as np

__all__ = [
    "AntipodalAxis",
    "LowEllPoleAnalysisSpec",
    "LowEllPoleEstimate",
    "IMPLEMENTED_HARMONIC_CONVENTION",
    "MIN_NUMERICAL_GAP_TOLERANCE",
    "PoleDefinition",
    "PoleStatus",
    "angular_momentum_power_tensor",
    "estimate_lowell_pole",
    "mean_squared_multipole_alignment",
    "scalar_alm_inversion_phase",
    "transform_antipodal_axis_o3",
    "transform_power_tensor_o3",
]


# A trace-one 3x3 tensor has O(1) eigenvalues.  Below this floor, roundoff from
# an exactly repeated eigenvalue can be larger than a caller's threshold.
MIN_NUMERICAL_GAP_TOLERANCE = float(64.0 * np.finfo(float).eps)
IMPLEMENTED_HARMONIC_CONVENTION = (
    "orthonormal Condon-Shortley dense real scalar map"
)


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


def _real_array(
    value: object,
    name: str,
    *,
    shape: tuple[int, ...],
) -> np.ndarray:
    if _contains_bool(value):
        raise ValueError(f"{name} must not contain booleans")
    if _contains_complex(value):
        raise ValueError(f"{name} must be real, not complex")
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if array.shape != shape or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite array with shape {shape}")
    return array


def _matrix_tuple(matrix: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in matrix)


def _array_content_identity(value: np.ndarray, *, role: str) -> str:
    array = np.ascontiguousarray(value, dtype="<f8")
    header = json.dumps(
        {
            "dtype": "<f8",
            "role": role,
            "schema": "LOWELL_NUMERIC_ARRAY_V1",
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


class PoleDefinition(str, Enum):
    """Implemented angular-momentum power-tensor pole definitions."""

    MAX_ANGULAR_MOMENTUM = "max_angular_momentum"
    MIN_ANGULAR_MOMENTUM = "min_angular_momentum"
    ANISOTROPY_TENSOR = "anisotropy_tensor"


class PoleStatus(str, Enum):
    """Whether the selected power-tensor eigendirection is unique."""

    IDENTIFIED = "identified"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class LowEllPoleAnalysisSpec:
    """Identity-bound configuration for one pole/alignment analysis."""

    ell_values: tuple[int, ...]
    definition: PoleDefinition
    gap_tolerance: float
    coordinate_frame: str
    harmonic_convention: str

    def __post_init__(self) -> None:
        if isinstance(self.ell_values, (str, bytes)):
            raise ValueError("ell_values must be an integer sequence")
        values = tuple(_validate_ell(value) for value in self.ell_values)
        if not values or len(set(values)) != len(values):
            raise ValueError("ell_values must be non-empty and distinct")
        if tuple(sorted(values)) != values:
            raise ValueError("ell_values must be strictly increasing")
        object.__setattr__(self, "ell_values", values)
        object.__setattr__(self, "definition", PoleDefinition(self.definition))
        object.__setattr__(
            self,
            "gap_tolerance",
            _validate_gap_tolerance(self.gap_tolerance),
        )
        for name in ("coordinate_frame", "harmonic_convention"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or value != value.strip():
                raise ValueError(f"{name} must be non-empty trimmed text")
        if self.harmonic_convention != IMPLEMENTED_HARMONIC_CONVENTION:
            raise ValueError(
                "harmonic_convention is not implemented by this kernel"
            )

    @property
    def analysis_id(self) -> str:
        payload = {
            "coordinate_frame": self.coordinate_frame,
            "definition": self.definition.value,
            "ell_values": list(self.ell_values),
            "gap_tolerance_hex": self.gap_tolerance.hex(),
            "harmonic_convention": self.harmonic_convention,
            "schema": "LOWELL_POLE_ANALYSIS_V1",
        }
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _selection_scores(
    eigenvalues: tuple[float, float, float] | np.ndarray,
    definition: PoleDefinition,
) -> np.ndarray:
    values = np.asarray(eigenvalues, dtype=float)
    if definition is PoleDefinition.MAX_ANGULAR_MOMENTUM:
        return values
    if definition is PoleDefinition.MIN_ANGULAR_MOMENTUM:
        return -values
    return np.abs(values - float(np.mean(values)))


def _selection_gap(
    eigenvalues: tuple[float, float, float] | np.ndarray,
    definition: PoleDefinition,
) -> float:
    scores = _selection_scores(eigenvalues, definition)
    score_order = np.argsort(scores, kind="stable")
    return max(
        0.0,
        float(scores[int(score_order[-1])] - scores[int(score_order[-2])]),
    )


@dataclass(frozen=True)
class AntipodalAxis:
    """A unit axis for which ``p`` and ``-p`` denote the same object."""

    representative: tuple[float, float, float]

    def __post_init__(self) -> None:
        vector = _real_array(
            self.representative,
            "axis representative",
            shape=(3,),
        )
        scale = float(np.max(np.abs(vector)))
        if scale == 0.0:
            raise ValueError("axis representative must be non-zero")
        scaled = vector / scale
        unit = scaled / float(np.linalg.norm(scaled))
        sign_pivot = int(np.argmax(np.abs(unit)))
        if unit[sign_pivot] < 0.0:
            unit = -unit
        unit[unit == 0.0] = 0.0
        object.__setattr__(
            self,
            "representative",
            tuple(float(component) for component in unit),
        )

    def abs_dot(self, other: AntipodalAxis) -> float:
        """Return the sign-invariant alignment in ``[0, 1]``."""

        if not isinstance(other, AntipodalAxis):
            raise TypeError("other must be an AntipodalAxis")
        dot = float(np.dot(self.representative, other.representative))
        return abs(float(np.clip(dot, -1.0, 1.0)))

    def separation_deg(self, other: AntipodalAxis) -> float:
        """Return the antipodal angular separation in degrees, in ``[0, 90]``."""

        return float(np.degrees(np.arccos(self.abs_dot(other))))


@dataclass(frozen=True)
class LowEllPoleEstimate:
    """A pole estimate and the numerical evidence for identifying its axis.

    Eigenvalues are ascending.  The selection gap and its tolerance are
    dimensionless because the angular-momentum power tensor has unit trace.
    """

    ell: int
    definition: PoleDefinition
    status: PoleStatus
    axis: AntipodalAxis | None
    eigenvalues: tuple[float, float, float]
    selection_gap: float
    gap_tolerance: float
    power_tensor: tuple[tuple[float, float, float], ...]
    analysis_spec: LowEllPoleAnalysisSpec

    def __post_init__(self) -> None:
        ell = _validate_ell(self.ell)
        definition = PoleDefinition(self.definition)
        status = PoleStatus(self.status)
        raw_values = _real_array(self.eigenvalues, "eigenvalues", shape=(3,))
        values = tuple(float(value) for value in raw_values)
        gap = float(self.selection_gap)
        tolerance = float(self.gap_tolerance)
        if not isinstance(self.analysis_spec, LowEllPoleAnalysisSpec):
            raise TypeError(
                "analysis_spec must be a LowEllPoleAnalysisSpec"
            )
        if values != tuple(sorted(values)):
            raise ValueError("eigenvalues must be in ascending order")
        if not math.isfinite(gap) or gap < 0.0:
            raise ValueError("selection_gap must be finite and non-negative")
        _validate_gap_tolerance(tolerance)
        if ell not in self.analysis_spec.ell_values:
            raise ValueError("ell must be registered in analysis_spec")
        if definition is not self.analysis_spec.definition:
            raise ValueError("definition must match analysis_spec")
        if tolerance != self.analysis_spec.gap_tolerance:
            raise ValueError("gap_tolerance must match analysis_spec")
        derived_gap = _selection_gap(values, definition)
        if gap != derived_gap:
            raise ValueError(
                "selection gap must be derived from eigenvalues and definition"
            )
        tensor = _real_array(
            self.power_tensor,
            "power_tensor",
            shape=(3, 3),
        )
        spectral_scale = float(np.max(np.abs(tensor), initial=0.0))
        tensor_tolerance = 128.0 * np.finfo(float).eps * max(
            spectral_scale, 1.0
        )
        if not np.allclose(
            tensor, tensor.T, atol=tensor_tolerance, rtol=0.0
        ):
            raise ValueError("power_tensor must be symmetric")
        if not math.isclose(
            float(np.trace(tensor)),
            1.0,
            abs_tol=tensor_tolerance,
            rel_tol=0.0,
        ):
            raise ValueError("power_tensor must have unit trace")
        derived_values, _ = np.linalg.eigh(tensor)
        if float(np.min(derived_values)) < -tensor_tolerance:
            raise ValueError("power_tensor must be positive semidefinite")
        if not np.allclose(
            derived_values,
            raw_values,
            atol=tensor_tolerance,
            rtol=0.0,
        ):
            raise ValueError(
                "eigenvalues must be derived from power_tensor"
            )
        if self.axis is not None and not isinstance(self.axis, AntipodalAxis):
            raise TypeError("axis must be an AntipodalAxis or None")
        object.__setattr__(self, "ell", ell)
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "eigenvalues", values)
        object.__setattr__(self, "selection_gap", gap)
        object.__setattr__(self, "gap_tolerance", tolerance)
        object.__setattr__(self, "power_tensor", _matrix_tuple(tensor))
        if (status is PoleStatus.IDENTIFIED) != (self.axis is not None):
            raise ValueError("identified status and axis presence must agree")
        if (status is PoleStatus.IDENTIFIED) != (gap > tolerance):
            raise ValueError("identified status must agree with the selection gap")
        if status is PoleStatus.IDENTIFIED:
            scores = _selection_scores(values, definition)
            selected_index = int(np.argsort(scores, kind="stable")[-1])
            axis_vector = np.asarray(self.axis.representative)
            eigen_residual = (
                tensor @ axis_vector
                - values[selected_index] * axis_vector
            )
            if float(np.linalg.norm(eigen_residual)) > tensor_tolerance:
                raise ValueError(
                    "identified axis must be the selected power-tensor "
                    "eigendirection"
                )

    @property
    def analysis_id(self) -> str:
        return self.analysis_spec.analysis_id

    @property
    def coordinate_frame(self) -> str:
        return self.analysis_spec.coordinate_frame

    @property
    def harmonic_convention(self) -> str:
        return self.analysis_spec.harmonic_convention

    @property
    def power_tensor_id(self) -> str:
        return _array_content_identity(
            np.asarray(self.power_tensor),
            role="lowell_power_tensor",
        )


def angular_momentum_power_tensor(
    *,
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    ell: int,
) -> np.ndarray:
    """Return the real symmetric trace-one power tensor for one multipole."""

    ell_i = _validate_ell(ell)
    alm = _dense_real_alm(alm_by_lm, ell=ell_i)
    norm = float(np.vdot(alm, alm).real)
    if norm == 0.0:
        raise ValueError("selected alm multipole has zero norm")

    generators = _angular_momentum_matrices(ell_i)
    tensor = np.empty((3, 3), dtype=float)
    normalization = float(ell_i * (ell_i + 1)) * norm
    for row in range(3):
        for column in range(row, 3):
            operator_ij = (
                generators[row] @ generators[column]
                + generators[column] @ generators[row]
            ) / 2.0
            value = float(np.vdot(alm, operator_ij @ alm).real / normalization)
            tensor[row, column] = value
            tensor[column, row] = value

    trace = float(np.trace(tensor))
    if not math.isfinite(trace) or trace <= 0.0:
        raise ValueError("power tensor normalization is not finite and positive")
    return tensor / trace


def estimate_lowell_pole(
    *,
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    ell: int,
    analysis_spec: LowEllPoleAnalysisSpec,
) -> LowEllPoleEstimate:
    """Estimate an antipodal pole, abstaining when its eigendirection is tied."""

    if not isinstance(analysis_spec, LowEllPoleAnalysisSpec):
        raise TypeError(
            "analysis_spec must be a LowEllPoleAnalysisSpec"
        )
    ell_i = _validate_ell(ell)
    if ell_i not in analysis_spec.ell_values:
        raise ValueError("ell must be registered in analysis_spec")
    definition_i = analysis_spec.definition
    tolerance = analysis_spec.gap_tolerance

    tensor = angular_momentum_power_tensor(alm_by_lm=alm_by_lm, ell=ell_i)
    eigenvalues, eigenvectors = np.linalg.eigh(tensor)
    scores = _selection_scores(eigenvalues, definition_i)
    score_order = np.argsort(scores, kind="stable")
    selected_index = int(score_order[-1])
    gap = _selection_gap(eigenvalues, definition_i)
    values_tuple = tuple(float(value) for value in eigenvalues)

    if gap <= tolerance:
        return LowEllPoleEstimate(
            ell=ell_i,
            definition=definition_i,
            status=PoleStatus.UNDETERMINED,
            axis=None,
            eigenvalues=values_tuple,
            selection_gap=gap,
            gap_tolerance=tolerance,
            power_tensor=_matrix_tuple(tensor),
            analysis_spec=analysis_spec,
        )

    return LowEllPoleEstimate(
        ell=ell_i,
        definition=definition_i,
        status=PoleStatus.IDENTIFIED,
        axis=AntipodalAxis(tuple(float(x) for x in eigenvectors[:, selected_index])),
        eigenvalues=values_tuple,
        selection_gap=gap,
        gap_tolerance=tolerance,
        power_tensor=_matrix_tuple(tensor),
        analysis_spec=analysis_spec,
    )


def mean_squared_multipole_alignment(
    *,
    estimates: Iterable[LowEllPoleEstimate],
) -> float | None:
    """Return the mean squared alignment across distinct multipole axes.

    The score is the mean of |p_i dot p_j| squared over all unordered pairs,
    so it is invariant to axis signs and a common rotation. Estimates must
    use one pole definition, distinct ell values, and a common coordinate
    frame. Return None if any requested pole is undetermined rather than
    silently selecting an identified subset. This is a descriptive geometric
    statistic, not a null calibration or significance estimate.
    """

    estimates_i = tuple(estimates)
    if len(estimates_i) < 2:
        raise ValueError("alignment requires at least two pole estimates")
    if not all(isinstance(item, LowEllPoleEstimate) for item in estimates_i):
        raise TypeError("estimates must contain only LowEllPoleEstimate values")
    if len({item.definition for item in estimates_i}) != 1:
        raise ValueError("alignment estimates must use the same pole definition")
    if len({item.analysis_id for item in estimates_i}) != 1:
        raise ValueError(
            "alignment estimates must use the same analysis identity"
        )
    if len({item.coordinate_frame for item in estimates_i}) != 1:
        raise ValueError(
            "alignment estimates must use the same coordinate frame"
        )
    if len({item.harmonic_convention for item in estimates_i}) != 1:
        raise ValueError(
            "alignment estimates must use the same harmonic convention"
        )
    ells = tuple(item.ell for item in estimates_i)
    if len(set(ells)) != len(ells):
        raise ValueError("alignment estimates must have distinct ell values")

    axes: list[AntipodalAxis] = []
    for estimate in estimates_i:
        if estimate.axis is None:
            return None
        axes.append(estimate.axis)

    pair_count = len(axes) * (len(axes) - 1) // 2
    pair_sum = math.fsum(
        left.abs_dot(right) ** 2
        for index, left in enumerate(axes[:-1])
        for right in axes[index + 1 :]
    )
    return float(pair_sum / pair_count)


def scalar_alm_inversion_phase(ell: int) -> int:
    """Return the parity factor ``(-1)^ell`` for a scalar multipole."""

    ell_i = _validate_ell(ell)
    return -1 if ell_i % 2 else 1


def _validate_o3_matrix(matrix: object) -> np.ndarray:
    value = _real_array(matrix, "O(3) matrix", shape=(3, 3))
    tolerance = 1e-10
    if not np.allclose(value.T @ value, np.eye(3), atol=tolerance, rtol=0.0):
        raise ValueError("O(3) matrix must be orthogonal")
    if not math.isclose(
        abs(float(np.linalg.det(value))),
        1.0,
        abs_tol=tolerance,
        rel_tol=0.0,
    ):
        raise ValueError("O(3) matrix determinant must be +/-1")
    return value


def transform_power_tensor_o3(tensor: object, matrix: object) -> np.ndarray:
    """Apply the tensor action ``T -> R T R^T`` for any O(3) matrix."""

    value = _real_array(tensor, "power tensor", shape=(3, 3))
    if not np.allclose(value, value.T, atol=1e-12, rtol=0.0):
        raise ValueError("power tensor must be symmetric")
    transform = _validate_o3_matrix(matrix)
    out = transform @ value @ transform.T
    return (out + out.T) / 2.0


def transform_antipodal_axis_o3(
    axis: AntipodalAxis,
    matrix: object,
) -> AntipodalAxis:
    """Transform an unoriented pole; inversion remains the same axis."""

    if not isinstance(axis, AntipodalAxis):
        raise TypeError("axis must be an AntipodalAxis")
    transform = _validate_o3_matrix(matrix)
    return AntipodalAxis(tuple(transform @ np.asarray(axis.representative)))


def _validate_ell(ell: int) -> int:
    if isinstance(ell, (bool, np.bool_)):
        raise ValueError("ell must be an integer >= 1")
    try:
        ell_i = operator.index(ell)
    except TypeError as exc:
        raise ValueError("ell must be an integer >= 1") from exc
    if ell_i < 1:
        raise ValueError("ell must be an integer >= 1")
    return int(ell_i)


def _validate_gap_tolerance(gap_tolerance: float) -> float:
    if isinstance(gap_tolerance, (bool, np.bool_)):
        raise ValueError("gap_tolerance must not be boolean")
    tolerance = float(gap_tolerance)
    if not math.isfinite(tolerance) or tolerance < MIN_NUMERICAL_GAP_TOLERANCE:
        raise ValueError(
            "gap_tolerance must be finite and at least "
            f"{MIN_NUMERICAL_GAP_TOLERANCE:.17g} for a trace-one 3x3 tensor"
        )
    return tolerance


def _dense_real_alm(
    alm_by_lm: Mapping[tuple[int, int], complex | float],
    *,
    ell: int,
) -> np.ndarray:
    selected: dict[int, complex] = {}
    for key, raw_value in alm_by_lm.items():
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError("alm_by_lm keys must be (ell, m) integer tuples")
        try:
            key_ell = operator.index(key[0])
            key_m = operator.index(key[1])
        except TypeError as exc:
            raise ValueError("alm_by_lm keys must be (ell, m) integer tuples") from exc
        if key_ell < 0 or abs(key_m) > key_ell:
            raise ValueError("alm_by_lm key has invalid ell/m")
        value = complex(raw_value)
        if not (math.isfinite(value.real) and math.isfinite(value.imag)):
            raise ValueError("alm coefficients must be finite")
        if key_ell == ell:
            selected[int(key_m)] = value

    expected = set(range(-ell, ell + 1))
    missing = sorted(expected - set(selected))
    if missing:
        raise ValueError(f"selected ell={ell} is missing m={missing}")
    alm = np.asarray(
        [selected[m] for m in range(-ell, ell + 1)],
        dtype=np.complex128,
    )
    scale = float(
        max(np.max(np.abs(alm.real)), np.max(np.abs(alm.imag)))
    )
    if scale == 0.0:
        raise ValueError("selected alm multipole has zero norm")
    alm = alm / scale
    relative_scale = float(np.max(np.abs(alm)))
    reality_tolerance = (
        128.0 * np.finfo(float).eps * float(2 * ell + 1) * relative_scale
    )
    if abs(float(alm[ell].imag)) > reality_tolerance:
        raise ValueError("alm coefficients violate the real-map reality condition")
    for m in range(1, ell + 1):
        expected_negative = ((-1) ** m) * np.conj(alm[ell + m])
        if abs(alm[ell - m] - expected_negative) > reality_tolerance:
            raise ValueError("alm coefficients violate the real-map reality condition")
    return alm


@lru_cache(maxsize=None)
def _angular_momentum_matrices(
    ell: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m_values = np.arange(-ell, ell + 1, dtype=float)
    size = 2 * ell + 1
    raising = np.zeros((size, size), dtype=np.complex128)
    for index, m_value in enumerate(m_values[:-1]):
        raising[index + 1, index] = np.sqrt(
            ell * (ell + 1) - m_value * (m_value + 1.0)
        )
    lowering = raising.T.conj()
    j_x = (raising + lowering) / 2.0
    j_y = (raising - lowering) / (2.0j)
    j_z = np.diag(m_values).astype(np.complex128)
    return j_x, j_y, j_z

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


@dataclass(frozen=True)
class AntipodalAxis:
    """A unit axis for which ``p`` and ``-p`` denote the same object."""

    representative: tuple[float, float, float]

    def __post_init__(self) -> None:
        if isinstance(self.representative, np.ndarray):
            has_bool = self.representative.dtype.kind == "b"
        else:
            has_bool = any(
                isinstance(value, (bool, np.bool_))
                for value in self.representative
            )
        if has_bool:
            raise ValueError("axis representative must not contain booleans")
        vector = np.asarray(self.representative, dtype=float)
        if vector.shape != (3,) or not np.isfinite(vector).all():
            raise ValueError("axis representative must be a finite 3-vector")
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

    def __post_init__(self) -> None:
        ell = _validate_ell(self.ell)
        definition = PoleDefinition(self.definition)
        status = PoleStatus(self.status)
        values = tuple(float(value) for value in self.eigenvalues)
        gap = float(self.selection_gap)
        tolerance = float(self.gap_tolerance)
        if len(values) != 3 or not all(math.isfinite(value) for value in values):
            raise ValueError("eigenvalues must contain three finite values")
        if values != tuple(sorted(values)):
            raise ValueError("eigenvalues must be in ascending order")
        if not math.isfinite(gap) or gap < 0.0:
            raise ValueError("selection_gap must be finite and non-negative")
        _validate_gap_tolerance(tolerance)
        if self.axis is not None and not isinstance(self.axis, AntipodalAxis):
            raise TypeError("axis must be an AntipodalAxis or None")
        object.__setattr__(self, "ell", ell)
        object.__setattr__(self, "definition", definition)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "eigenvalues", values)
        object.__setattr__(self, "selection_gap", gap)
        object.__setattr__(self, "gap_tolerance", tolerance)
        if (status is PoleStatus.IDENTIFIED) != (self.axis is not None):
            raise ValueError("identified status and axis presence must agree")
        if (status is PoleStatus.IDENTIFIED) != (gap > tolerance):
            raise ValueError("identified status must agree with the selection gap")


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
    definition: PoleDefinition | str,
    gap_tolerance: float,
) -> LowEllPoleEstimate:
    """Estimate an antipodal pole, abstaining when its eigendirection is tied."""

    ell_i = _validate_ell(ell)
    definition_i = PoleDefinition(definition)
    tolerance = _validate_gap_tolerance(gap_tolerance)

    tensor = angular_momentum_power_tensor(alm_by_lm=alm_by_lm, ell=ell_i)
    eigenvalues, eigenvectors = np.linalg.eigh(tensor)
    if definition_i is PoleDefinition.MAX_ANGULAR_MOMENTUM:
        scores = eigenvalues
    elif definition_i is PoleDefinition.MIN_ANGULAR_MOMENTUM:
        scores = -eigenvalues
    else:
        scores = np.abs(eigenvalues - float(np.mean(eigenvalues)))

    score_order = np.argsort(scores, kind="stable")
    selected_index = int(score_order[-1])
    runner_up_index = int(score_order[-2])
    gap = max(0.0, float(scores[selected_index] - scores[runner_up_index]))
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
        )

    return LowEllPoleEstimate(
        ell=ell_i,
        definition=definition_i,
        status=PoleStatus.IDENTIFIED,
        axis=AntipodalAxis(tuple(float(x) for x in eigenvectors[:, selected_index])),
        eigenvalues=values_tuple,
        selection_gap=gap,
        gap_tolerance=tolerance,
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
    if isinstance(matrix, np.ndarray):
        has_bool = matrix.dtype.kind == "b"
    elif isinstance(matrix, (tuple, list)):
        has_bool = any(
            isinstance(value, (bool, np.bool_))
            for row in matrix
            for value in (row if isinstance(row, (tuple, list)) else (row,))
        )
    else:
        has_bool = isinstance(matrix, (bool, np.bool_))
    if has_bool:
        raise ValueError("O(3) matrix must not contain booleans")
    value = np.asarray(matrix, dtype=float)
    if value.shape != (3, 3) or not np.isfinite(value).all():
        raise ValueError("O(3) matrix must be a finite 3x3 matrix")
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

    value = np.asarray(tensor, dtype=float)
    if value.shape != (3, 3) or not np.isfinite(value).all():
        raise ValueError("power tensor must be a finite 3x3 matrix")
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

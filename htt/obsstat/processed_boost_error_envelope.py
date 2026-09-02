"""Matrix-valued numerical-error envelope for PMG-WU-011 Task-7C A4.

The registered controls are numerical perturbation matrices that are already
expressed in the scientific stored-real metrics.  This module preserves their
output-direction structure instead of collapsing them to one scalar operator
norm.  It does not define a physical high-multipole prior, fit an observer
velocity, or authorize a scientific containment terminal.

For one control family ``E_i`` and any unit coefficient vector ``b``,

    E(b) E(b)^T <= sum_i E_i E_i^T

in Loewner order.  For an additive sum of ``q`` independently registered
families, Cauchy--Schwarz gives the conservative envelope

    C_E = q * sum_{family,i} E_{family,i} E_{family,i}^T + lambda^2 I.

If an unknown numerical perturbation obeys ``Delta Delta^T <= C_E``, then
``||C_E^{-1/2} Delta||_2 <= 1``.  Weyl's singular-value inequality therefore
implies

    sigma_j(C_E^{-1/2} K_true)
        >= sigma_j(C_E^{-1/2} K_observed) - 1.

Only singular values separated safely above one certify numerical rank.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping

import numpy as np


class MatrixErrorEnvelopeError(ValueError):
    """Raised when an A4 numerical-error-envelope contract fails closed."""


class RankCertificateStatus(str, Enum):
    """Typed status of an error-whitened numerical rank certificate."""

    FULL_ROW_RANK_CERTIFIED = "FULL_ROW_RANK_CERTIFIED"
    PARTIAL_RANK_CERTIFIED = "PARTIAL_RANK_CERTIFIED"
    THRESHOLD_AMBIGUOUS = "THRESHOLD_AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class MatrixValuedErrorEnvelope:
    """Positive-definite output-space envelope for numerical perturbations."""

    output_covariance: np.ndarray
    inverse_square_root: np.ndarray
    eigenvalues: np.ndarray
    regularization_scale: float
    output_dimension: int
    source_dimension: int
    family_count: int
    family_shapes: Mapping[str, tuple[int, int, int]]
    maximum_registered_normalized_norm: float

    def __post_init__(self) -> None:
        if self.output_dimension <= 0 or self.source_dimension <= 0:
            raise MatrixErrorEnvelopeError("error-envelope dimensions are invalid")
        if self.family_count <= 0:
            raise MatrixErrorEnvelopeError("error-envelope family registry is empty")
        if not math.isfinite(self.regularization_scale) or self.regularization_scale <= 0.0:
            raise MatrixErrorEnvelopeError("error-envelope regularization is invalid")
        if (
            self.output_covariance.shape
            != (self.output_dimension, self.output_dimension)
            or self.inverse_square_root.shape
            != (self.output_dimension, self.output_dimension)
            or self.eigenvalues.shape != (self.output_dimension,)
        ):
            raise MatrixErrorEnvelopeError("error-envelope arrays have inconsistent shapes")
        if (
            not np.all(np.isfinite(self.output_covariance))
            or not np.all(np.isfinite(self.inverse_square_root))
            or not np.all(np.isfinite(self.eigenvalues))
            or np.any(self.eigenvalues <= 0.0)
        ):
            raise MatrixErrorEnvelopeError("error-envelope arrays are not finite positive")
        if not math.isfinite(self.maximum_registered_normalized_norm):
            raise MatrixErrorEnvelopeError("registered control normalization is invalid")


@dataclass(frozen=True)
class ErrorWhitenedRankCertificate:
    """Weyl-safe lower certificate for the row rank of one observed matrix."""

    status: RankCertificateStatus
    error_whitened_singular_values: np.ndarray
    singular_value_lower_bounds: np.ndarray
    guaranteed_rank_lower_bound: int
    full_row_rank_certified: bool
    smallest_singular_value: float
    ambiguity_half_width: float

    def __post_init__(self) -> None:
        if self.guaranteed_rank_lower_bound < 0:
            raise MatrixErrorEnvelopeError("guaranteed rank is negative")
        if not (0.0 < self.ambiguity_half_width < 1.0):
            raise MatrixErrorEnvelopeError("rank ambiguity width is outside its domain")
        if (
            self.error_whitened_singular_values.ndim != 1
            or self.singular_value_lower_bounds.shape
            != self.error_whitened_singular_values.shape
            or not np.all(np.isfinite(self.error_whitened_singular_values))
            or not np.all(np.isfinite(self.singular_value_lower_bounds))
        ):
            raise MatrixErrorEnvelopeError("rank-certificate spectrum is invalid")


def _sealed(values: object) -> np.ndarray:
    array = np.ascontiguousarray(np.asarray(values, dtype="<f8"))
    sealed = np.frombuffer(array.tobytes(), dtype="<f8").reshape(array.shape)
    sealed.setflags(write=False)
    return sealed


def _finite_family(value: object, *, label: str) -> np.ndarray:
    try:
        family = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise MatrixErrorEnvelopeError(f"{label} is not a finite matrix family") from exc
    if (
        family.ndim != 3
        or min(family.shape) <= 0
        or not np.all(np.isfinite(family))
    ):
        raise MatrixErrorEnvelopeError(f"{label} is not a finite matrix family")
    return family


def _finite_matrix(value: object, *, label: str) -> np.ndarray:
    try:
        matrix = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise MatrixErrorEnvelopeError(f"{label} is not a finite matrix") from exc
    if matrix.ndim != 2 or min(matrix.shape) <= 0 or not np.all(np.isfinite(matrix)):
        raise MatrixErrorEnvelopeError(f"{label} is not a finite matrix")
    return matrix


def build_output_error_envelope(
    control_families: Mapping[str, object],
    *,
    reference_operator_norm: float,
    regularization_relative: float = 1.0e-12,
    machine_safety_factor: float = 64.0,
) -> MatrixValuedErrorEnvelope:
    """Build a conservative positive-definite output-space error envelope.

    Every family has shape ``(n_variants, n_output, n_source)``.  A family may
    represent Cartesian full-sky replay controls, resolution differences,
    map-to-alm iteration differences, or another separately registered
    numerical perturbation mechanism.  All matrices must use the same output
    and source coordinates.

    The multiplier equal to the number of additive families follows from
    ``||sum_f y_f||^2 <= q sum_f ||y_f||^2``.  It is conservative and explicit;
    correlations may be modelled more sharply only by a successor contract.
    """

    if not isinstance(control_families, Mapping) or not control_families:
        raise MatrixErrorEnvelopeError("control-family registry is empty")
    if (
        not math.isfinite(reference_operator_norm)
        or reference_operator_norm <= 0.0
        or not math.isfinite(regularization_relative)
        or regularization_relative <= 0.0
        or not math.isfinite(machine_safety_factor)
        or machine_safety_factor <= 0.0
    ):
        raise MatrixErrorEnvelopeError("error-envelope scale policy is invalid")

    parsed: list[tuple[str, np.ndarray]] = []
    common_shape: tuple[int, int] | None = None
    shape_registry: dict[str, tuple[int, int, int]] = {}
    for raw_name, raw_family in control_families.items():
        if not isinstance(raw_name, str) or not raw_name:
            raise MatrixErrorEnvelopeError("control-family name is absent")
        family = _finite_family(raw_family, label=f"control family {raw_name}")
        matrix_shape = (family.shape[1], family.shape[2])
        if common_shape is None:
            common_shape = matrix_shape
        elif matrix_shape != common_shape:
            raise MatrixErrorEnvelopeError("control families use different matrix shapes")
        parsed.append((raw_name, family))
        shape_registry[raw_name] = tuple(int(item) for item in family.shape)

    assert common_shape is not None
    output_dimension, source_dimension = common_shape
    covariance_sum = np.zeros((output_dimension, output_dimension), dtype=np.float64)
    for _name, family in parsed:
        for matrix in family:
            covariance_sum += matrix @ matrix.T

    family_count = len(parsed)
    regularization_scale = max(
        regularization_relative * reference_operator_norm,
        machine_safety_factor
        * np.finfo(np.float64).eps
        * max(output_dimension, source_dimension)
        * reference_operator_norm,
    )
    covariance = (
        family_count * covariance_sum
        + regularization_scale**2 * np.eye(output_dimension, dtype=np.float64)
    )
    covariance = 0.5 * (covariance + covariance.T)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if np.any(eigenvalues <= 0.0) or not np.all(np.isfinite(eigenvalues)):
        raise MatrixErrorEnvelopeError("numerical error envelope is not positive definite")
    inverse_square_root = (
        eigenvectors
        @ np.diag(1.0 / np.sqrt(eigenvalues))
        @ eigenvectors.T
    )
    inverse_square_root = 0.5 * (inverse_square_root + inverse_square_root.T)

    maximum_normalized = 0.0
    for _name, family in parsed:
        for matrix in family:
            singular = np.linalg.svd(inverse_square_root @ matrix, compute_uv=False)
            if singular.size:
                maximum_normalized = max(maximum_normalized, float(singular[0]))
    if maximum_normalized > 1.0 + 2.0e-10:
        raise MatrixErrorEnvelopeError("registered control escapes its error envelope")

    return MatrixValuedErrorEnvelope(
        output_covariance=_sealed(covariance),
        inverse_square_root=_sealed(inverse_square_root),
        eigenvalues=_sealed(eigenvalues),
        regularization_scale=float(regularization_scale),
        output_dimension=output_dimension,
        source_dimension=source_dimension,
        family_count=family_count,
        family_shapes=MappingProxyType(shape_registry),
        maximum_registered_normalized_norm=maximum_normalized,
    )


def certify_error_whitened_row_rank(
    observed_matrix: object,
    envelope: MatrixValuedErrorEnvelope,
    *,
    ambiguity_half_width: float = 0.10,
) -> ErrorWhitenedRankCertificate:
    """Return the row-rank lower bound certified above the error envelope.

    If ``K_obs = K_true + Delta`` and ``Delta Delta^T <= C_E``, then each
    singular value of ``C_E^{-1/2} K_true`` is at least the corresponding
    observed singular value minus one.  A singular value must exceed
    ``1 + ambiguity_half_width`` to count toward the guaranteed rank.
    """

    if type(envelope) is not MatrixValuedErrorEnvelope:
        raise MatrixErrorEnvelopeError("rank certificate requires an exact envelope")
    if (
        not math.isfinite(ambiguity_half_width)
        or not 0.0 < ambiguity_half_width < 1.0
    ):
        raise MatrixErrorEnvelopeError("rank ambiguity width is outside its domain")

    observed = _finite_matrix(observed_matrix, label="observed response")
    if observed.shape != (envelope.output_dimension, envelope.source_dimension):
        raise MatrixErrorEnvelopeError("observed response shape differs from the envelope")

    whitened = envelope.inverse_square_root @ observed
    singular_values = np.linalg.svd(whitened, compute_uv=False)
    lower_bounds = np.maximum(singular_values - 1.0, 0.0)
    guaranteed_rank = int(
        np.count_nonzero(singular_values > 1.0 + ambiguity_half_width)
    )
    near_boundary = bool(
        np.any(
            (singular_values >= 1.0 - ambiguity_half_width)
            & (singular_values <= 1.0 + ambiguity_half_width)
        )
    )
    full_row_possible = observed.shape[1] >= observed.shape[0]
    full_row_rank = bool(
        full_row_possible
        and singular_values.size >= observed.shape[0]
        and guaranteed_rank == observed.shape[0]
    )

    if full_row_rank:
        status = RankCertificateStatus.FULL_ROW_RANK_CERTIFIED
    elif near_boundary:
        status = RankCertificateStatus.THRESHOLD_AMBIGUOUS
    elif guaranteed_rank > 0:
        status = RankCertificateStatus.PARTIAL_RANK_CERTIFIED
    else:
        status = RankCertificateStatus.UNRESOLVED

    smallest = float(singular_values[-1]) if singular_values.size else 0.0
    return ErrorWhitenedRankCertificate(
        status=status,
        error_whitened_singular_values=_sealed(singular_values),
        singular_value_lower_bounds=_sealed(lower_bounds),
        guaranteed_rank_lower_bound=guaranteed_rank,
        full_row_rank_certified=full_row_rank,
        smallest_singular_value=smallest,
        ambiguity_half_width=float(ambiguity_half_width),
    )


__all__ = [
    "ErrorWhitenedRankCertificate",
    "MatrixErrorEnvelopeError",
    "MatrixValuedErrorEnvelope",
    "RankCertificateStatus",
    "build_output_error_envelope",
    "certify_error_whitened_row_rank",
]

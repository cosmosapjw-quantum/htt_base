"""Control-floor-safe image geometry for PMG-WU-011 Task-7C.

This module consumes matrices that are already expressed in the scientific
stored-real metrics.  It does not build sky maps, fit an observer velocity, or
assign physical amplitudes to the high-multipole source.  Its sole purpose is
to keep numerical replay floors from being promoted to resolved nuisance
subspaces and to expose the exact finite-dimensional containment witness

    rank(P_{Im K}^perp J) = rank([K J]) - rank(K).

The matched full-sky control is an engineering numerical control, not a prior
on the physical high-ell sky.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

import numpy as np


class RankPolicyError(ValueError):
    """Raised when a Task-7C rank-policy input violates its contract."""


class RankDecisionStatus(str, Enum):
    """Resolution status of a control-anchored numerical image rank."""

    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class RankPolicy:
    """Numerical controls for metric-whitened low/high image geometry."""

    relative_singular_ceiling: float = 1.0e-10
    control_safety_factor: float = 5.0
    machine_safety_factor: float = 64.0
    ambiguity_factor: float = 2.0

    def __post_init__(self) -> None:
        values = (
            self.relative_singular_ceiling,
            self.control_safety_factor,
            self.machine_safety_factor,
            self.ambiguity_factor,
        )
        if not all(math.isfinite(value) and value > 0.0 for value in values):
            raise RankPolicyError("rank-policy values must be finite and positive")
        if self.ambiguity_factor <= 1.0:
            raise RankPolicyError("ambiguity factor must exceed one")


@dataclass(frozen=True)
class ImageBasisDecision:
    """Thresholded orthonormal image basis and its numerical provenance."""

    basis: np.ndarray
    singular_values: np.ndarray
    threshold: float
    rank: int
    status: RankDecisionStatus
    control_operator_norm: float


@dataclass(frozen=True)
class ControlAnchoredNuisanceGeometry:
    """Low response after quotienting by a control-resolved nuisance image."""

    rank_status: RankDecisionStatus
    low_rank: int
    high_rank: int
    surviving_rank: int | None
    augmented_rank_increment: int | None
    rank_identity_holds: bool | None
    containment_witness: bool | None
    surviving_frobenius_fraction: float | None
    low_threshold: float
    high_threshold: float
    high_control_operator_norm: float
    high_singular_values: np.ndarray
    surviving_low_matrix: np.ndarray | None


def high_source_dimension(cutoff: int) -> int:
    """Return sum_{ell=7}^cutoff (2 ell + 1) = (L-6)(L+8)."""

    if type(cutoff) is not int or cutoff < 7:
        raise RankPolicyError("source cutoff must be an integer at least seven")
    return (cutoff - 6) * (cutoff + 8)


def _sealed(array: np.ndarray) -> np.ndarray:
    value = np.frombuffer(
        np.ascontiguousarray(array, dtype="<f8").tobytes(),
        dtype="<f8",
    ).reshape(array.shape)
    value.setflags(write=False)
    return value


def _finite_matrix(value: object, *, label: str) -> np.ndarray:
    try:
        matrix = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise RankPolicyError(f"{label} is not a finite matrix") from exc
    if matrix.ndim != 2 or not np.all(np.isfinite(matrix)):
        raise RankPolicyError(f"{label} is not a finite matrix")
    return matrix


def _operator_norm(singular_values: np.ndarray) -> float:
    return float(singular_values[0]) if singular_values.size else 0.0


def _machine_floor(matrix: np.ndarray, reference_scale: float, policy: RankPolicy) -> float:
    return (
        policy.machine_safety_factor
        * np.finfo(np.float64).eps
        * max(matrix.shape, default=0)
        * reference_scale
    )


def _basis_at_threshold(
    matrix: np.ndarray,
    singular_values: np.ndarray,
    threshold: float,
) -> tuple[np.ndarray, int]:
    if matrix.shape[1] == 0 or singular_values.size == 0:
        return _sealed(np.zeros((matrix.shape[0], 0), dtype=np.float64)), 0
    left, _, _ = np.linalg.svd(matrix, full_matrices=False)
    rank = int(np.count_nonzero(singular_values > threshold))
    return _sealed(left[:, :rank]), rank


def _low_image_basis(
    low_matrix: np.ndarray,
    policy: RankPolicy,
) -> ImageBasisDecision:
    singular = np.linalg.svd(low_matrix, compute_uv=False)
    scale = _operator_norm(singular)
    if scale <= 0.0:
        raise RankPolicyError("low response must have nonzero operator norm")
    threshold = max(
        policy.relative_singular_ceiling * scale,
        _machine_floor(low_matrix, scale, policy),
    )
    basis, rank = _basis_at_threshold(low_matrix, singular, threshold)
    return ImageBasisDecision(
        basis=basis,
        singular_values=_sealed(singular),
        threshold=float(threshold),
        rank=rank,
        status=RankDecisionStatus.RESOLVED,
        control_operator_norm=0.0,
    )


def control_anchored_image_basis(
    high_matrix: object,
    matched_fullsky_control: object,
    *,
    low_operator_norm: float,
    policy: RankPolicy = RankPolicy(),
) -> ImageBasisDecision:
    """Resolve a nuisance image against relative, control, and machine floors.

    ``matched_fullsky_control`` must have the same shape and numerical settings
    as the high-source matrix except for the full-sky mask that makes the exact
    retained high-source response vanish.  This routine treats its operator
    norm as a conservative replay-floor anchor.
    """

    high = _finite_matrix(high_matrix, label="high response")
    control = _finite_matrix(matched_fullsky_control, label="full-sky control")
    if high.shape != control.shape:
        raise RankPolicyError("matched full-sky control has the wrong shape")
    if not math.isfinite(low_operator_norm) or low_operator_norm <= 0.0:
        raise RankPolicyError("low operator norm must be finite and positive")

    singular = np.linalg.svd(high, compute_uv=False)
    control_singular = np.linalg.svd(control, compute_uv=False)
    high_scale = _operator_norm(singular)
    control_scale = _operator_norm(control_singular)
    threshold = max(
        policy.relative_singular_ceiling * high_scale,
        policy.control_safety_factor * control_scale,
        _machine_floor(high, low_operator_norm, policy),
    )

    lower = threshold / policy.ambiguity_factor
    upper = threshold * policy.ambiguity_factor
    ambiguous = bool(np.any((singular >= lower) & (singular <= upper)))
    basis, rank = _basis_at_threshold(high, singular, threshold)
    return ImageBasisDecision(
        basis=basis,
        singular_values=_sealed(singular),
        threshold=float(threshold),
        rank=rank,
        status=(
            RankDecisionStatus.AMBIGUOUS
            if ambiguous
            else RankDecisionStatus.RESOLVED
        ),
        control_operator_norm=control_scale,
    )


def _rank_of_orthonormal_union(
    first: np.ndarray,
    second: np.ndarray,
    policy: RankPolicy,
) -> int:
    union = np.concatenate((first, second), axis=1)
    if union.shape[1] == 0:
        return 0
    singular = np.linalg.svd(union, compute_uv=False)
    threshold = max(
        policy.relative_singular_ceiling,
        policy.machine_safety_factor
        * np.finfo(np.float64).eps
        * max(union.shape),
    )
    return int(np.count_nonzero(singular > threshold))


def analyse_control_anchored_nuisance_geometry(
    low_matrix: object,
    high_matrix: object,
    matched_fullsky_control: object,
    *,
    policy: RankPolicy = RankPolicy(),
) -> ControlAnchoredNuisanceGeometry:
    """Compute a fail-closed low/high image quotient.

    Inputs must already be metric-whitened.  An ambiguous high-source rank is
    returned without a scientific containment decision.
    """

    low = _finite_matrix(low_matrix, label="low response")
    high = _finite_matrix(high_matrix, label="high response")
    control = _finite_matrix(
        matched_fullsky_control,
        label="matched full-sky control",
    )
    if high.shape != control.shape or low.shape[0] != high.shape[0]:
        raise RankPolicyError("low/high/control output dimensions do not match")

    low_image = _low_image_basis(low, policy)
    low_operator_norm = _operator_norm(low_image.singular_values)
    high_image = control_anchored_image_basis(
        high,
        control,
        low_operator_norm=low_operator_norm,
        policy=policy,
    )

    if high_image.status is RankDecisionStatus.AMBIGUOUS:
        return ControlAnchoredNuisanceGeometry(
            rank_status=RankDecisionStatus.AMBIGUOUS,
            low_rank=low_image.rank,
            high_rank=high_image.rank,
            surviving_rank=None,
            augmented_rank_increment=None,
            rank_identity_holds=None,
            containment_witness=None,
            surviving_frobenius_fraction=None,
            low_threshold=low_image.threshold,
            high_threshold=high_image.threshold,
            high_control_operator_norm=high_image.control_operator_norm,
            high_singular_values=high_image.singular_values,
            surviving_low_matrix=None,
        )

    projector = (
        np.eye(low.shape[0], dtype=np.float64)
        - high_image.basis @ high_image.basis.T
    )
    survivor = projector @ low
    survivor_singular = np.linalg.svd(survivor, compute_uv=False)
    surviving_rank = int(
        np.count_nonzero(survivor_singular > low_image.threshold)
    )
    low_frobenius = float(np.linalg.norm(low, ord="fro"))
    surviving_fraction = float(
        np.linalg.norm(survivor, ord="fro") / low_frobenius
    )

    augmented_rank = _rank_of_orthonormal_union(
        high_image.basis,
        low_image.basis,
        policy,
    )
    increment = augmented_rank - high_image.rank
    identity_holds = surviving_rank == increment
    containment = surviving_rank == 0 and increment == 0

    return ControlAnchoredNuisanceGeometry(
        rank_status=RankDecisionStatus.RESOLVED,
        low_rank=low_image.rank,
        high_rank=high_image.rank,
        surviving_rank=surviving_rank,
        augmented_rank_increment=increment,
        rank_identity_holds=identity_holds,
        containment_witness=containment,
        surviving_frobenius_fraction=surviving_fraction,
        low_threshold=low_image.threshold,
        high_threshold=high_image.threshold,
        high_control_operator_norm=high_image.control_operator_norm,
        high_singular_values=high_image.singular_values,
        surviving_low_matrix=_sealed(survivor),
    )

"""Directional nuisance-span contracts for PMG-WU-011 Task-7C.

This module extends the synthetic processed local-observer scalar response from
Task-7B.  It contracts the registered Cartesian response along fixed observer
boost directions, applies the scientific stored-real metrics, and asks whether
any low-source response survives projection orthogonal to an unrestricted
high-multipole nuisance image.

It does not fit an observer velocity, choose a high-multipole prior, construct
a source-coefficient pseudoinverse, or alter the strict-positive finite-sky
production path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .processed_boost_response import ProcessedBoostError


DIRECTION_IDS = ("X", "Y", "Z", "D111", "D1M11", "D11M1")
CORE_SOURCE_CUTOFFS = (9, 12, 16)
RANK_RELATIVE_THRESHOLD = 1.0e-10
_RANK_SHELL_ULPS = 1024.0
_GEOMETRY_SCHEMA = "HTT_WU011_TASK7C_DIRECTIONAL_NUISANCE_GEOMETRY_V1"


class Task7CTerminal(str, Enum):
    """Typed terminals for source-band convergence and nuisance geometry."""

    PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE = (
        "PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE"
    )
    PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE = (
        "PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE"
    )
    PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED = (
        "PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED"
    )
    BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE = (
        "BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE"
    )
    BLOCKED_BY_CUTOFF_CONSTRUCTION = "BLOCKED_BY_CUTOFF_CONSTRUCTION"
    BLOCKED_BY_ARTIFACT_INTEGRITY = "BLOCKED_BY_ARTIFACT_INTEGRITY"


def _sealed_array(values: object, *, shape: tuple[int, ...], label: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(f"{label} has the wrong finite shape") from exc
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ProcessedBoostError(f"{label} has the wrong finite shape")
    return np.frombuffer(
        np.ascontiguousarray(array, dtype="<f8").tobytes(), dtype="<f8"
    ).reshape(shape)


def _content_id(role: str, payload: Mapping[str, object], *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    )
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(b"\0")
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(b"\0")
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _sealed_direction(values: tuple[float, float, float]) -> np.ndarray:
    vector = np.asarray(values, dtype="<f8")
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError("Task-7C direction must be a finite three-vector")
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ProcessedBoostError("Task-7C direction must have positive norm")
    unit = np.ascontiguousarray(vector / norm, dtype="<f8")
    unit.flags.writeable = False
    return unit


_DIRECTION_REGISTRY: Mapping[str, np.ndarray] = MappingProxyType(
    {
        "X": _sealed_direction((1.0, 0.0, 0.0)),
        "Y": _sealed_direction((0.0, 1.0, 0.0)),
        "Z": _sealed_direction((0.0, 0.0, 1.0)),
        "D111": _sealed_direction((1.0, 1.0, 1.0)),
        "D1M11": _sealed_direction((1.0, -1.0, 1.0)),
        "D11M1": _sealed_direction((1.0, 1.0, -1.0)),
    }
)


def direction_registry() -> Mapping[str, np.ndarray]:
    """Return the immutable, sign-nonredundant unit-direction registry."""

    return _DIRECTION_REGISTRY


def _finite_unit_direction(direction: object) -> np.ndarray:
    try:
        vector = np.asarray(direction, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError("direction must be a finite unit three-vector") from exc
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ProcessedBoostError("direction must be a finite unit three-vector")
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or abs(norm - 1.0) > 2.0e-14:
        raise ProcessedBoostError("direction must be a finite unit three-vector")
    return vector


def contract_directional_tensor(tensor: object, direction: object) -> np.ndarray:
    """Contract ``(axis, output, source)`` along one unit boost direction."""

    try:
        array = np.asarray(tensor, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            "directional response tensor must have finite shape (3,m,n)"
        ) from exc
    if array.ndim != 3 or array.shape[0] != 3 or not np.all(np.isfinite(array)):
        raise ProcessedBoostError(
            "directional response tensor must have finite shape (3,m,n)"
        )
    vector = _finite_unit_direction(direction)
    contracted = np.einsum("i,ioj->oj", vector, array)
    return _sealed_array(
        contracted,
        shape=array.shape[1:],
        label="directionally contracted response matrix",
    )


def metric_whiten_directional_matrix(
    matrix: object,
    *,
    source_metric_diagonal: object,
    output_metric_diagonal: object,
) -> np.ndarray:
    """Return the invariant stored-real representation of a directional map."""

    try:
        raw = np.asarray(matrix, dtype=np.float64)
        source_metric = np.asarray(source_metric_diagonal, dtype=np.float64)
        output_metric = np.asarray(output_metric_diagonal, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(
            "directional metric inputs must be finite real arrays"
        ) from exc
    if raw.ndim != 2 or not np.all(np.isfinite(raw)):
        raise ProcessedBoostError("directional response matrix must be finite and rank two")
    if (
        source_metric.shape != (raw.shape[1],)
        or output_metric.shape != (raw.shape[0],)
        or not np.all(np.isfinite(source_metric))
        or not np.all(np.isfinite(output_metric))
        or np.any(source_metric <= 0.0)
        or np.any(output_metric <= 0.0)
    ):
        raise ProcessedBoostError(
            "directional metric diagonals must be finite, positive, and dimension matched"
        )
    whitened = (
        np.sqrt(output_metric)[:, None]
        * raw
        / np.sqrt(source_metric)[None, :]
    )
    return _sealed_array(
        whitened,
        shape=raw.shape,
        label="metric-whitened directional response matrix",
    )


@dataclass(frozen=True)
class _ImageBasis:
    basis: np.ndarray
    singular_values: tuple[float, ...]
    rank: int
    threshold: float


def _image_basis(
    matrix: np.ndarray,
    *,
    reference_scale: float | None = None,
) -> _ImageBasis:
    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise ProcessedBoostError("image-basis matrix must be finite and rank two")
    u, singular, _ = np.linalg.svd(array, full_matrices=False)
    if singular.size == 0:
        return _ImageBasis(
            basis=np.zeros((array.shape[0], 0), dtype=np.float64),
            singular_values=(),
            rank=0,
            threshold=0.0,
        )
    largest = float(singular[0])
    scale = largest if reference_scale is None else float(reference_scale)
    if not math.isfinite(scale) or scale < 0.0:
        raise ProcessedBoostError("rank reference scale must be finite and nonnegative")
    if scale <= np.finfo(float).tiny:
        threshold = 0.0
        rank = 0
    else:
        threshold = RANK_RELATIVE_THRESHOLD * scale
        shell = _RANK_SHELL_ULPS * np.finfo(float).eps * scale
        positive = singular[singular > 0.0]
        if positive.size and np.any(np.abs(positive - threshold) <= shell):
            raise ProcessedBoostError("singular value lies on the rank threshold shell")
        rank = int(np.count_nonzero(singular > threshold))
    basis = np.asarray(u[:, :rank], dtype=np.float64)
    return _ImageBasis(
        basis=_sealed_array(
            basis,
            shape=(array.shape[0], rank),
            label="orthonormal image basis",
        ),
        singular_values=tuple(float(value) for value in singular),
        rank=rank,
        threshold=float(threshold),
    )


@dataclass(frozen=True)
class DirectionalNuisanceGeometry:
    """Model-free image geometry for one direction and one source cutoff."""

    direction_id: str
    source_cutoff: int
    low_rank: int
    high_rank: int
    surviving_rank: int
    low_singular_values: tuple[float, ...]
    high_singular_values: tuple[float, ...]
    surviving_singular_values: tuple[float, ...]
    surviving_frobenius_fraction: float
    minimum_principal_angle_degrees: float
    maximum_principal_angle_degrees: float
    nuisance_projector: np.ndarray
    surviving_low_matrix: np.ndarray
    content_id: str


def analyse_whitened_nuisance_geometry(
    low_matrix: object,
    high_matrix: object,
    *,
    direction_id: str,
    source_cutoff: int,
) -> DirectionalNuisanceGeometry:
    """Project the low response outside the unrestricted high-source image."""

    if direction_id not in DIRECTION_IDS:
        raise ProcessedBoostError("Task-7C direction ID is outside the registry")
    if type(source_cutoff) is not int or source_cutoff < 7:
        raise ProcessedBoostError("Task-7C source cutoff is outside its domain")
    try:
        low = np.asarray(low_matrix, dtype=np.float64)
        high = np.asarray(high_matrix, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError("low/high response matrices must be finite") from exc
    if (
        low.ndim != 2
        or high.ndim != 2
        or low.shape[0] != high.shape[0]
        or not np.all(np.isfinite(low))
        or not np.all(np.isfinite(high))
    ):
        raise ProcessedBoostError(
            "low/high response matrices must be finite and share their output dimension"
        )
    low_image = _image_basis(low)
    high_image = _image_basis(high)
    output_dimension = low.shape[0]
    projector = np.eye(output_dimension) - high_image.basis @ high_image.basis.T
    projector = 0.5 * (projector + projector.T)
    survivor = projector @ low
    survivor_image = _image_basis(
        survivor,
        reference_scale=(
            float(low_image.singular_values[0]) if low_image.singular_values else 0.0
        ),
    )
    low_norm = float(np.linalg.norm(low))
    survivor_norm = float(np.linalg.norm(survivor))
    fraction = 0.0 if low_norm <= np.finfo(float).tiny else survivor_norm / low_norm
    fraction = min(1.0, max(0.0, float(fraction)))

    if low_image.rank == 0 or high_image.rank == 0:
        minimum_angle = 90.0
        maximum_angle = 90.0
    else:
        overlap = low_image.basis.T @ high_image.basis
        cosines = np.linalg.svd(overlap, compute_uv=False)
        cosines = np.clip(cosines, 0.0, 1.0)
        angles = np.degrees(np.arccos(cosines))
        minimum_angle = float(np.min(angles))
        maximum_angle = float(np.max(angles))

    sealed_projector = _sealed_array(
        projector,
        shape=(output_dimension, output_dimension),
        label="high-source orthogonal-complement projector",
    )
    sealed_survivor = _sealed_array(
        survivor,
        shape=low.shape,
        label="surviving low-source response",
    )
    content_id = _content_id(
        _GEOMETRY_SCHEMA,
        {
            "direction_id": direction_id,
            "source_cutoff": source_cutoff,
            "low_rank": low_image.rank,
            "high_rank": high_image.rank,
            "surviving_rank": survivor_image.rank,
            "surviving_frobenius_fraction_hex": fraction.hex(),
            "minimum_principal_angle_degrees_hex": minimum_angle.hex(),
            "maximum_principal_angle_degrees_hex": maximum_angle.hex(),
            "rank_relative_threshold_hex": RANK_RELATIVE_THRESHOLD.hex(),
        },
        low,
        high,
        sealed_projector,
        sealed_survivor,
    )
    return DirectionalNuisanceGeometry(
        direction_id=direction_id,
        source_cutoff=source_cutoff,
        low_rank=low_image.rank,
        high_rank=high_image.rank,
        surviving_rank=survivor_image.rank,
        low_singular_values=low_image.singular_values,
        high_singular_values=high_image.singular_values,
        surviving_singular_values=survivor_image.singular_values,
        surviving_frobenius_fraction=fraction,
        minimum_principal_angle_degrees=minimum_angle,
        maximum_principal_angle_degrees=maximum_angle,
        nuisance_projector=sealed_projector,
        surviving_low_matrix=sealed_survivor,
        content_id=content_id,
    )


__all__ = [
    "CORE_SOURCE_CUTOFFS",
    "DIRECTION_IDS",
    "DirectionalNuisanceGeometry",
    "ProcessedBoostError",
    "RANK_RELATIVE_THRESHOLD",
    "Task7CTerminal",
    "analyse_whitened_nuisance_geometry",
    "contract_directional_tensor",
    "direction_registry",
    "metric_whiten_directional_matrix",
]

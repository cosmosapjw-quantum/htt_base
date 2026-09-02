"""Directional nuisance-span contracts for PMG-WU-011 Task-7C.

This module extends the synthetic processed local-observer scalar response from
Task-7B. It contracts the registered Cartesian response along fixed observer
boost directions, applies the scientific stored-real metrics, extends the
source band, and asks whether any low-source response survives projection
orthogonal to an unrestricted high-multipole nuisance image.

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
import re
from types import MappingProxyType
from typing import Mapping

import numpy as np

from .planck_pr3_operator import build_joint_cutsky_operator, fit_joint_cutsky_alm
from .processed_boost_identifiability import (
    _MAP2ALM_ITERATIONS,
    _linear_generator_from_alm,
    _mask_for,
    _mode_alm,
    _operator_norm,
    _output_metric,
    _stored_real_metric,
    _transfer_arrays,
)
from .processed_boost_jacobian import (
    build_processed_boost_jacobian,
    metric_whitened_matrix,
)
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    ProcessedBoostError,
    joint_to_scientific_real,
)


DIRECTION_IDS = ("X", "Y", "Z", "D111", "D1M11", "D11M1")
CORE_SOURCE_CUTOFFS = (9, 12, 16)
SMOKE_CASE_IDS = ("WIDE_N8_IDENTITY", "FULL_N8_IDENTITY")
CI_CORE_CASE_IDS = (
    "WIDE_N16_IDENTITY",
    "WIDE_N32_IDENTITY",
    "FULL_N16_IDENTITY",
    "REFERENCE_N16_GAUSSIAN",
)
RANK_RELATIVE_THRESHOLD = 1.0e-10
SOURCE_LAST_FROBENIUS_FRACTION_CEILING = 0.10
SOURCE_LAST_OPERATOR_FRACTION_CEILING = 0.10
SURVIVING_FRACTION_DRIFT_CEILING = 0.02
_RANK_SHELL_ULPS = 1024.0
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_GEOMETRY_SCHEMA = "HTT_WU011_TASK7C_DIRECTIONAL_NUISANCE_GEOMETRY_V1"
_SOURCE_BLOCK_SCHEMA = "HTT_WU011_TASK7C_EXTENDED_SOURCE_BLOCK_V1"
_DIRECTIONAL_RESULT_SCHEMA = "HTT_WU011_TASK7C_DIRECTIONAL_RESULT_V1"
_CASE_SCHEMA = "HTT_WU011_TASK7C_CASE_V1"
_ATLAS_SCHEMA = "HTT_WU011_TASK7C_ATLAS_V1"


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


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - optional dependency gate
        raise ProcessedBoostError(
            "healpy is required for the WU-011 Task-7C atlas"
        ) from exc
    return hp


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


@dataclass(frozen=True)
class Task7COperatorSpec:
    case_id: str
    nside: int
    processing_lmax: int
    mask_kind: str
    transfer_kind: str
    source_cutoffs: tuple[int, ...]

    def __post_init__(self) -> None:
        hp = _healpy()
        if self.case_id not in SMOKE_CASE_IDS + CI_CORE_CASE_IDS:
            raise ProcessedBoostError("Task-7C case ID is outside the registry")
        if type(self.nside) is not int or not hp.isnsideok(self.nside, nest=False):
            raise ProcessedBoostError("Task-7C nside is invalid")
        if (
            type(self.processing_lmax) is not int
            or self.processing_lmax < 8
            or self.processing_lmax > 3 * self.nside - 1
        ):
            raise ProcessedBoostError("Task-7C processing lmax is invalid")
        if (
            not self.source_cutoffs
            or tuple(sorted(set(self.source_cutoffs))) != self.source_cutoffs
            or min(self.source_cutoffs) < 8
            or max(self.source_cutoffs) + 1 > self.processing_lmax
        ):
            raise ProcessedBoostError(
                "Task-7C processing lmax must include every raised source cutoff"
            )


def task7c_case_specs(profile: str) -> tuple[Task7COperatorSpec, ...]:
    if profile == "SMOKE":
        return (
            Task7COperatorSpec(
                case_id="WIDE_N8_IDENTITY",
                nside=8,
                processing_lmax=10,
                mask_kind="APODIZED_Z_WIDE",
                transfer_kind="IDENTITY",
                source_cutoffs=(8, 9),
            ),
            Task7COperatorSpec(
                case_id="FULL_N8_IDENTITY",
                nside=8,
                processing_lmax=9,
                mask_kind="FULL",
                transfer_kind="IDENTITY",
                source_cutoffs=(8,),
            ),
        )
    if profile == "CI_CORE":
        return (
            Task7COperatorSpec(
                case_id="WIDE_N16_IDENTITY",
                nside=16,
                processing_lmax=17,
                mask_kind="APODIZED_Z_WIDE",
                transfer_kind="IDENTITY",
                source_cutoffs=CORE_SOURCE_CUTOFFS,
            ),
            Task7COperatorSpec(
                case_id="WIDE_N32_IDENTITY",
                nside=32,
                processing_lmax=13,
                mask_kind="APODIZED_Z_WIDE",
                transfer_kind="IDENTITY",
                source_cutoffs=(12,),
            ),
            Task7COperatorSpec(
                case_id="FULL_N16_IDENTITY",
                nside=16,
                processing_lmax=13,
                mask_kind="FULL",
                transfer_kind="IDENTITY",
                source_cutoffs=(12,),
            ),
            Task7COperatorSpec(
                case_id="REFERENCE_N16_GAUSSIAN",
                nside=16,
                processing_lmax=13,
                mask_kind="APODIZED_Z_REFERENCE",
                transfer_kind="REFERENCE_GAUSSIAN",
                source_cutoffs=(12,),
            ),
        )
    raise ProcessedBoostError("Task-7C profile is outside the registry")


def _build_operator(spec: Task7COperatorSpec) -> ProcessedBoostOperator:
    mask = _mask_for(spec.nside, spec.mask_kind)
    joint = build_joint_cutsky_operator(
        mask,
        lmin=0,
        lmax=FIT_LMAX,
        retained_lmin=RETAINED_LMIN,
    )
    source_beam, source_pixel, target_beam, target_pixel = _transfer_arrays(
        spec.processing_lmax,
        spec.transfer_kind,
    )
    return ProcessedBoostOperator.from_components(
        mask=mask,
        joint_operator=joint,
        processing_lmax=spec.processing_lmax,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )


def task7c_smoke_operator(*, processing_lmax: int = 10) -> ProcessedBoostOperator:
    if type(processing_lmax) is not int or not 8 <= processing_lmax <= 23:
        raise ProcessedBoostError("Task-7C smoke processing lmax is invalid")
    spec = Task7COperatorSpec(
        case_id="WIDE_N8_IDENTITY",
        nside=8,
        processing_lmax=processing_lmax,
        mask_kind="APODIZED_Z_WIDE",
        transfer_kind="IDENTITY",
        source_cutoffs=(processing_lmax - 1,),
    )
    return _build_operator(spec)


@dataclass(frozen=True)
class Task7CSourceBlock:
    source_ell: int
    tensor: np.ndarray
    metric_whitened_matrix: np.ndarray
    source_metric_diagonal: np.ndarray
    metric_frobenius_norm: float
    metric_operator_norm: float
    singular_values: tuple[float, ...]
    operator_id: str
    content_id: str

    def __post_init__(self) -> None:
        width = 2 * self.source_ell + 1
        tensor = _sealed_array(
            self.tensor,
            shape=(3, 32, width),
            label="Task-7C extended source tensor",
        )
        whitened = _sealed_array(
            self.metric_whitened_matrix,
            shape=(96, width),
            label="Task-7C extended source whitened matrix",
        )
        metric = _sealed_array(
            self.source_metric_diagonal,
            shape=(width,),
            label="Task-7C extended source metric",
        )
        if not self.operator_id.startswith("sha256:") or not self.content_id.startswith(
            "sha256:"
        ):
            raise ProcessedBoostError("Task-7C source block lacks content identity")
        if (
            not math.isfinite(self.metric_frobenius_norm)
            or self.metric_frobenius_norm < 0.0
            or not math.isfinite(self.metric_operator_norm)
            or self.metric_operator_norm < 0.0
        ):
            raise ProcessedBoostError("Task-7C source-block norms are invalid")
        object.__setattr__(self, "tensor", tensor)
        object.__setattr__(self, "metric_whitened_matrix", whitened)
        object.__setattr__(self, "source_metric_diagonal", metric)


def _build_source_block(
    operator: ProcessedBoostOperator,
    *,
    source_ell: int,
) -> Task7CSourceBlock:
    hp = _healpy()
    if type(operator) is not ProcessedBoostOperator:
        raise ProcessedBoostError("Task-7C source block requires a processed operator")
    if type(source_ell) is not int or source_ell < 7:
        raise ProcessedBoostError("Task-7C source ell is outside its domain")
    if operator.processing_lmax < source_ell + 1:
        raise ProcessedBoostError(
            "Task-7C processing lmax must include the raised source band"
        )
    width = 2 * source_ell + 1
    tensor = np.empty((3, 32, width), dtype=np.float64)
    source_transfer = operator.source_beam * operator.source_pixel_window
    for mode_index in range(width):
        alm = _mode_alm(source_ell, mode_index, operator.processing_lmax)
        for axis, beta in enumerate(np.eye(3, dtype=np.float64)):
            generator = _linear_generator_from_alm(alm, operator, beta)
            generator_alm = hp.map2alm(
                generator,
                lmax=operator.processing_lmax,
                iter=_MAP2ALM_ITERATIONS,
                pol=False,
            )
            filtered_alm = hp.almxfl(
                generator_alm,
                source_transfer,
                inplace=False,
            )
            pixel_map = hp.alm2map(
                filtered_alm,
                nside=operator.nside,
                lmax=operator.processing_lmax,
                pol=False,
            )
            fit = fit_joint_cutsky_alm(
                np.asarray(pixel_map, dtype=np.float64),
                mask=operator.mask,
                operator=operator.joint_operator,
                source_beam=operator.source_beam,
                source_pixel_window=operator.source_pixel_window,
                target_beam=operator.target_beam,
                target_pixel_window=operator.target_pixel_window,
            )
            tensor[axis, :, mode_index] = joint_to_scientific_real(
                fit.retained_coefficients,
                lmin=RETAINED_LMIN,
                lmax=FIT_LMAX,
            )
    source_metric = _stored_real_metric(source_ell)
    whitened = metric_whitened_matrix(
        tensor.reshape(96, width),
        source_metric_diagonal=source_metric,
        output_metric_diagonal=np.tile(_output_metric(), 3),
    )
    singular = tuple(
        float(value) for value in np.linalg.svd(whitened, compute_uv=False)
    )
    frobenius = float(np.linalg.norm(whitened))
    operator_norm = _operator_norm(whitened)
    content_id = _content_id(
        _SOURCE_BLOCK_SCHEMA,
        {
            "source_ell": source_ell,
            "operator_id": operator.content_id,
            "map2alm_iterations": _MAP2ALM_ITERATIONS,
        },
        tensor,
        whitened,
        source_metric,
    )
    return Task7CSourceBlock(
        source_ell=source_ell,
        tensor=tensor,
        metric_whitened_matrix=whitened,
        source_metric_diagonal=source_metric,
        metric_frobenius_norm=frobenius,
        metric_operator_norm=operator_norm,
        singular_values=singular,
        operator_id=operator.content_id,
        content_id=content_id,
    )


class ExtendedSourceBlockCache:
    """Per-operator cache that prevents rebuilding a source ell per direction."""

    def __init__(self) -> None:
        self._blocks: dict[tuple[str, int], Task7CSourceBlock] = {}
        self._build_count = 0

    @property
    def build_count(self) -> int:
        return self._build_count

    def get(
        self,
        operator: ProcessedBoostOperator,
        *,
        source_ell: int,
    ) -> Task7CSourceBlock:
        if type(operator) is not ProcessedBoostOperator:
            raise ProcessedBoostError("Task-7C cache requires a processed operator")
        if type(source_ell) is not int or source_ell < 7:
            raise ProcessedBoostError("Task-7C cache source ell is outside its domain")
        if operator.processing_lmax < source_ell + 1:
            raise ProcessedBoostError(
                "Task-7C processing lmax must include the raised source band"
            )
        key = (operator.content_id, source_ell)
        if key not in self._blocks:
            self._blocks[key] = _build_source_block(operator, source_ell=source_ell)
            self._build_count += 1
        return self._blocks[key]


@dataclass(frozen=True)
class Task7CBlockNorm:
    source_ell: int
    metric_frobenius_norm: float
    metric_operator_norm: float
    block_id: str


@dataclass(frozen=True)
class Task7CDirectionalResult:
    case_id: str
    direction_id: str
    source_cutoff: int
    low_matrix: np.ndarray
    high_matrix: np.ndarray
    geometry: DirectionalNuisanceGeometry
    block_norms: tuple[Task7CBlockNorm, ...]
    last_block_frobenius_fraction: float
    last_block_operator_fraction: float
    surviving_sector_fractions: tuple[float, ...]
    numerical_floor_control: bool
    content_id: str

    def __post_init__(self) -> None:
        high_width = (self.source_cutoff + 1) ** 2 - 49
        low = _sealed_array(
            self.low_matrix,
            shape=(32, 48),
            label="Task-7C directional low response",
        )
        high = _sealed_array(
            self.high_matrix,
            shape=(32, high_width),
            label="Task-7C directional high response",
        )
        if len(self.surviving_sector_fractions) != 6:
            raise ProcessedBoostError("Task-7C survivor sector registry is incomplete")
        if not self.content_id.startswith("sha256:"):
            raise ProcessedBoostError("Task-7C directional result lacks content identity")
        object.__setattr__(self, "low_matrix", low)
        object.__setattr__(self, "high_matrix", high)


@dataclass(frozen=True)
class Task7CCaseResult:
    case_id: str
    nside: int
    processing_lmax: int
    mask_kind: str
    transfer_kind: str
    source_cutoffs: tuple[int, ...]
    operator_id: str
    jacobian_id: str
    directional_results: tuple[Task7CDirectionalResult, ...]
    source_block_ids: tuple[str, ...]
    content_id: str

    def result(self, direction_id: str, source_cutoff: int) -> Task7CDirectionalResult:
        for item in self.directional_results:
            if item.direction_id == direction_id and item.source_cutoff == source_cutoff:
                return item
        raise ProcessedBoostError("Task-7C directional result is absent")


def _surviving_sector_fractions(surviving: np.ndarray) -> tuple[float, ...]:
    total_square = float(np.linalg.norm(surviving) ** 2)
    if total_square <= np.finfo(float).tiny:
        return (0.0,) * 6
    values: list[float] = []
    cursor = 0
    for ell in range(1, 7):
        width = 2 * ell + 1
        block = surviving[:, cursor : cursor + width]
        values.append(float(np.linalg.norm(block) ** 2 / total_square))
        cursor += width
    values[-1] += 1.0 - sum(values)
    return tuple(values)


def build_task7c_case(
    spec: Task7COperatorSpec,
    *,
    cache: ExtendedSourceBlockCache | None = None,
) -> Task7CCaseResult:
    if type(spec) is not Task7COperatorSpec:
        raise ProcessedBoostError("Task-7C case requires an exact case spec")
    active_cache = cache if cache is not None else ExtendedSourceBlockCache()
    operator = _build_operator(spec)
    jacobian = build_processed_boost_jacobian(operator)
    low_tensor = np.asarray(jacobian.tensor[:, :, 1:], dtype=np.float64)
    low_source_metric = np.asarray(
        jacobian.source_metric_diagonal[1:], dtype=np.float64
    )
    output_metric = np.asarray(jacobian.output_metric_diagonal, dtype=np.float64)
    maximum_cutoff = max(spec.source_cutoffs)
    blocks = tuple(
        active_cache.get(operator, source_ell=ell)
        for ell in range(7, maximum_cutoff + 1)
    )
    results: list[Task7CDirectionalResult] = []
    for cutoff in spec.source_cutoffs:
        active_blocks = tuple(block for block in blocks if block.source_ell <= cutoff)
        for direction_id in DIRECTION_IDS:
            direction = _DIRECTION_REGISTRY[direction_id]
            low_raw = contract_directional_tensor(low_tensor, direction)
            low = metric_whiten_directional_matrix(
                low_raw,
                source_metric_diagonal=low_source_metric,
                output_metric_diagonal=output_metric,
            )
            directional_blocks: list[np.ndarray] = []
            block_norms: list[Task7CBlockNorm] = []
            for block in active_blocks:
                raw = contract_directional_tensor(block.tensor, direction)
                whitened = metric_whiten_directional_matrix(
                    raw,
                    source_metric_diagonal=block.source_metric_diagonal,
                    output_metric_diagonal=output_metric,
                )
                directional_blocks.append(whitened)
                block_norms.append(
                    Task7CBlockNorm(
                        source_ell=block.source_ell,
                        metric_frobenius_norm=float(np.linalg.norm(whitened)),
                        metric_operator_norm=_operator_norm(whitened),
                        block_id=block.content_id,
                    )
                )
            high = np.concatenate(directional_blocks, axis=1)
            geometry = analyse_whitened_nuisance_geometry(
                low,
                high,
                direction_id=direction_id,
                source_cutoff=cutoff,
            )
            high_frobenius = float(np.linalg.norm(high))
            high_operator = _operator_norm(high)
            last_frobenius = block_norms[-1].metric_frobenius_norm
            last_operator = block_norms[-1].metric_operator_norm
            last_frobenius_fraction = (
                0.0
                if high_frobenius <= np.finfo(float).tiny
                else last_frobenius / high_frobenius
            )
            last_operator_fraction = (
                0.0
                if high_operator <= np.finfo(float).tiny
                else last_operator / high_operator
            )
            survivor_fractions = _surviving_sector_fractions(
                geometry.surviving_low_matrix
            )
            low_norm = float(np.linalg.norm(low))
            numerical_floor = bool(
                high_frobenius
                <= 1.0e-8 * max(low_norm, np.finfo(float).tiny)
            )
            result_id = _content_id(
                _DIRECTIONAL_RESULT_SCHEMA,
                {
                    "case_id": spec.case_id,
                    "direction_id": direction_id,
                    "source_cutoff": cutoff,
                    "operator_id": operator.content_id,
                    "jacobian_id": jacobian.content_id,
                    "geometry_id": geometry.content_id,
                    "block_ids": [item.block_id for item in block_norms],
                    "last_block_frobenius_fraction_hex": (
                        float(last_frobenius_fraction).hex()
                    ),
                    "last_block_operator_fraction_hex": (
                        float(last_operator_fraction).hex()
                    ),
                    "surviving_sector_fraction_hex": [
                        float(value).hex() for value in survivor_fractions
                    ],
                    "numerical_floor_control": numerical_floor,
                },
                low,
                high,
                geometry.surviving_low_matrix,
            )
            results.append(
                Task7CDirectionalResult(
                    case_id=spec.case_id,
                    direction_id=direction_id,
                    source_cutoff=cutoff,
                    low_matrix=low,
                    high_matrix=high,
                    geometry=geometry,
                    block_norms=tuple(block_norms),
                    last_block_frobenius_fraction=float(
                        last_frobenius_fraction
                    ),
                    last_block_operator_fraction=float(last_operator_fraction),
                    surviving_sector_fractions=survivor_fractions,
                    numerical_floor_control=numerical_floor,
                    content_id=result_id,
                )
            )
    case_id = _content_id(
        _CASE_SCHEMA,
        {
            "case_id": spec.case_id,
            "nside": spec.nside,
            "processing_lmax": spec.processing_lmax,
            "mask_kind": spec.mask_kind,
            "transfer_kind": spec.transfer_kind,
            "source_cutoffs": list(spec.source_cutoffs),
            "operator_id": operator.content_id,
            "jacobian_id": jacobian.content_id,
            "directional_result_ids": [item.content_id for item in results],
            "source_block_ids": [block.content_id for block in blocks],
        },
    )
    return Task7CCaseResult(
        case_id=spec.case_id,
        nside=spec.nside,
        processing_lmax=spec.processing_lmax,
        mask_kind=spec.mask_kind,
        transfer_kind=spec.transfer_kind,
        source_cutoffs=spec.source_cutoffs,
        operator_id=operator.content_id,
        jacobian_id=jacobian.content_id,
        directional_results=tuple(results),
        source_block_ids=tuple(block.content_id for block in blocks),
        content_id=case_id,
    )


@dataclass(frozen=True)
class Task7CConvergenceRecord:
    direction_id: str
    lower_cutoff: int
    upper_cutoff: int
    lower_high_rank: int
    upper_high_rank: int
    lower_surviving_rank: int
    upper_surviving_rank: int
    lower_surviving_fraction: float
    upper_surviving_fraction: float
    upper_last_frobenius_fraction: float
    upper_last_operator_fraction: float


def classify_task7c_convergence(
    records: tuple[Task7CConvergenceRecord, ...],
) -> Task7CTerminal:
    if (
        len(records) != len(DIRECTION_IDS)
        or tuple(record.direction_id for record in records) != DIRECTION_IDS
    ):
        raise ProcessedBoostError("Task-7C convergence direction registry differs")
    for record in records:
        if type(record) is not Task7CConvergenceRecord:
            raise ProcessedBoostError("Task-7C convergence record type differs")
        values = (
            record.lower_surviving_fraction,
            record.upper_surviving_fraction,
            record.upper_last_frobenius_fraction,
            record.upper_last_operator_fraction,
        )
        if (
            record.lower_cutoff >= record.upper_cutoff
            or any(rank < 0 for rank in (
                record.lower_high_rank,
                record.upper_high_rank,
                record.lower_surviving_rank,
                record.upper_surviving_rank,
            ))
            or not all(math.isfinite(value) and value >= 0.0 for value in values)
        ):
            raise ProcessedBoostError("Task-7C convergence record is invalid")
    converged = all(
        record.lower_high_rank == record.upper_high_rank
        and record.lower_surviving_rank == record.upper_surviving_rank
        and abs(
            record.upper_surviving_fraction
            - record.lower_surviving_fraction
        )
        <= SURVIVING_FRACTION_DRIFT_CEILING
        and record.upper_last_frobenius_fraction
        <= SOURCE_LAST_FROBENIUS_FRACTION_CEILING
        and record.upper_last_operator_fraction
        <= SOURCE_LAST_OPERATOR_FRACTION_CEILING
        for record in records
    )
    if not converged:
        return Task7CTerminal.PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED
    upper_ranks = tuple(record.upper_surviving_rank for record in records)
    if all(rank == 0 for rank in upper_ranks):
        return Task7CTerminal.PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE
    if all(rank > 0 for rank in upper_ranks):
        return Task7CTerminal.PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE
    return Task7CTerminal.BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE


def _convergence_records(
    case: Task7CCaseResult,
    *,
    lower_cutoff: int,
    upper_cutoff: int,
) -> tuple[Task7CConvergenceRecord, ...]:
    records: list[Task7CConvergenceRecord] = []
    for direction_id in DIRECTION_IDS:
        lower = case.result(direction_id, lower_cutoff)
        upper = case.result(direction_id, upper_cutoff)
        records.append(
            Task7CConvergenceRecord(
                direction_id=direction_id,
                lower_cutoff=lower_cutoff,
                upper_cutoff=upper_cutoff,
                lower_high_rank=lower.geometry.high_rank,
                upper_high_rank=upper.geometry.high_rank,
                lower_surviving_rank=lower.geometry.surviving_rank,
                upper_surviving_rank=upper.geometry.surviving_rank,
                lower_surviving_fraction=(
                    lower.geometry.surviving_frobenius_fraction
                ),
                upper_surviving_fraction=(
                    upper.geometry.surviving_frobenius_fraction
                ),
                upper_last_frobenius_fraction=(
                    upper.last_block_frobenius_fraction
                ),
                upper_last_operator_fraction=(
                    upper.last_block_operator_fraction
                ),
            )
        )
    return tuple(records)


@dataclass(frozen=True)
class Task7CAtlas:
    source_revision: str
    profile: str
    cases: tuple[Task7CCaseResult, ...]
    terminal: Task7CTerminal
    convergence_records: tuple[Task7CConvergenceRecord, ...]
    source_block_build_count: int
    content_id: str

    def scalar_record(self) -> dict[str, object]:
        return {
            "schema": _ATLAS_SCHEMA,
            "source_revision": self.source_revision,
            "profile": self.profile,
            "terminal": self.terminal.value,
            "case_ids": [case.case_id for case in self.cases],
            "case_content_ids": [case.content_id for case in self.cases],
            "source_block_build_count": self.source_block_build_count,
            "content_id": self.content_id,
            "raw_planck_execution": False,
            "empirical_beta_fit": False,
            "claim_promotion": False,
            "merge_authorized": False,
        }


def build_task7c_atlas(*, source_revision: str, profile: str) -> Task7CAtlas:
    if _REVISION_RE.fullmatch(source_revision) is None:
        raise ProcessedBoostError("Task-7C source revision must be a full Git SHA")
    specs = task7c_case_specs(profile)
    cache = ExtendedSourceBlockCache()
    cases = tuple(build_task7c_case(spec, cache=cache) for spec in specs)
    primary = cases[0]
    if len(primary.source_cutoffs) < 2:
        raise ProcessedBoostError("Task-7C primary case lacks convergence cutoffs")
    lower_cutoff, upper_cutoff = primary.source_cutoffs[-2:]
    convergence = _convergence_records(
        primary,
        lower_cutoff=lower_cutoff,
        upper_cutoff=upper_cutoff,
    )
    terminal = classify_task7c_convergence(convergence)
    atlas_id = _content_id(
        _ATLAS_SCHEMA,
        {
            "source_revision": source_revision,
            "profile": profile,
            "case_ids": [case.case_id for case in cases],
            "case_content_ids": [case.content_id for case in cases],
            "terminal": terminal.value,
            "convergence": [
                {
                    "direction_id": record.direction_id,
                    "lower_cutoff": record.lower_cutoff,
                    "upper_cutoff": record.upper_cutoff,
                    "lower_high_rank": record.lower_high_rank,
                    "upper_high_rank": record.upper_high_rank,
                    "lower_surviving_rank": record.lower_surviving_rank,
                    "upper_surviving_rank": record.upper_surviving_rank,
                    "lower_surviving_fraction_hex": (
                        record.lower_surviving_fraction.hex()
                    ),
                    "upper_surviving_fraction_hex": (
                        record.upper_surviving_fraction.hex()
                    ),
                    "upper_last_frobenius_fraction_hex": (
                        record.upper_last_frobenius_fraction.hex()
                    ),
                    "upper_last_operator_fraction_hex": (
                        record.upper_last_operator_fraction.hex()
                    ),
                }
                for record in convergence
            ],
            "source_block_build_count": cache.build_count,
        },
    )
    return Task7CAtlas(
        source_revision=source_revision,
        profile=profile,
        cases=cases,
        terminal=terminal,
        convergence_records=convergence,
        source_block_build_count=cache.build_count,
        content_id=atlas_id,
    )


__all__ = [
    "CI_CORE_CASE_IDS",
    "CORE_SOURCE_CUTOFFS",
    "DIRECTION_IDS",
    "DirectionalNuisanceGeometry",
    "ExtendedSourceBlockCache",
    "ProcessedBoostError",
    "RANK_RELATIVE_THRESHOLD",
    "SMOKE_CASE_IDS",
    "SOURCE_LAST_FROBENIUS_FRACTION_CEILING",
    "SOURCE_LAST_OPERATOR_FRACTION_CEILING",
    "SURVIVING_FRACTION_DRIFT_CEILING",
    "Task7CAtlas",
    "Task7CBlockNorm",
    "Task7CCaseResult",
    "Task7CConvergenceRecord",
    "Task7CDirectionalResult",
    "Task7COperatorSpec",
    "Task7CSourceBlock",
    "Task7CTerminal",
    "analyse_whitened_nuisance_geometry",
    "build_task7c_atlas",
    "build_task7c_case",
    "classify_task7c_convergence",
    "contract_directional_tensor",
    "direction_registry",
    "metric_whiten_directional_matrix",
    "task7c_case_specs",
    "task7c_smoke_operator",
]

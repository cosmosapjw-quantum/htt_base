"""Cut-sky identifiability and source-band sensitivity atlas for PMG-WU-011.

This Task-7B module characterizes the already reviewed synthetic processed
local-observer scalar boost response. It varies only registered synthetic
masks and transfer functions, decomposes the metric-whitened response by source
multipole, and constructs separately typed signed first-order leakage blocks
for source ``ell=7..9``. The strict-positive finite-sky API remains frozen at
``ell<=6`` and no observed data or empirical velocity fit is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Mapping

import numpy as np

from .planck_pr3_operator import build_joint_cutsky_operator, fit_joint_cutsky_alm
from .processed_boost_jacobian import (
    build_processed_boost_jacobian,
    metric_whitened_matrix,
)
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    ProcessedBoostError,
    healpix_sky_directions,
    joint_to_scientific_real,
)


_IDENTIFIABILITY_SCHEMA = "HTT_WU011_TASK7B_IDENTIFIABILITY_ATLAS_V1"
_CASE_SCHEMA = "HTT_WU011_TASK7B_CASE_V1"
_EXTENDED_BLOCK_SCHEMA = "HTT_WU011_TASK7B_EXTENDED_SOURCE_BLOCK_V1"
_EXTENDED_TAIL_SCHEMA = "HTT_WU011_TASK7B_EXTENDED_TAIL_V1"
_TERMINAL_SCHEMA = "HTT_WU011_TASK7B_TERMINAL_V1"
_ARTIFACT_SCHEMA = "HTT_WU011_TASK7B_ARTIFACT_SET_V1"
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_MAP2ALM_ITERATIONS = 3
_SECTOR_SUM_ATOL = 2.0e-12
_RANK_RELATIVE_THRESHOLD = 1.0e-10
_CANDIDATE_CONDITION_CEILING = 100.0
_CANDIDATE_ALIAS_RATIO_CEILING = 1.0
_CANDIDATE_TAIL_RATIO_CEILING = 1.0

CI_CORE_CASE_IDS = (
    "FULL_IDENTITY",
    "BINARY_Z_IDENTITY",
    "APODIZED_Z_NARROW_IDENTITY",
    "APODIZED_Z_REFERENCE_IDENTITY",
    "APODIZED_Z_WIDE_IDENTITY",
    "APODIZED_Z_REFERENCE_MATCHED_GAUSSIAN",
    "APODIZED_Z_REFERENCE_GAUSSIAN",
)


class Task7BTerminal(str, Enum):
    """Typed terminal states for the Task-7B characterization node."""

    PASS_TASK7B_ATLAS_CANDIDATE_FOUND = "PASS_TASK7B_ATLAS_CANDIDATE_FOUND"
    PASS_TASK7B_ATLAS_NO_CANDIDATE = "PASS_TASK7B_ATLAS_NO_CANDIDATE"
    BLOCKED_BY_CASE_CONSTRUCTION = "BLOCKED_BY_CASE_CONSTRUCTION"
    BLOCKED_BY_METRIC_INCONSISTENCY = "BLOCKED_BY_METRIC_INCONSISTENCY"
    BLOCKED_BY_EXTENDED_BAND_FAILURE = "BLOCKED_BY_EXTENDED_BAND_FAILURE"
    BLOCKED_BY_ARTIFACT_INTEGRITY = "BLOCKED_BY_ARTIFACT_INTEGRITY"


def _healpy():
    try:
        import healpy as hp
    except ImportError as exc:  # pragma: no cover - optional dependency gate
        raise ProcessedBoostError(
            "healpy is required for the WU-011 Task-7B atlas"
        ) from exc
    return hp


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _content_id(role: str, payload: Mapping[str, object], *arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(_canonical_json(payload))
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(b"\0")
        digest.update(value.dtype.str.encode("ascii"))
        digest.update(b"\0")
        digest.update(repr(value.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(memoryview(value).cast("B"))
    return "sha256:" + digest.hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sealed(values: object, *, shape: tuple[int, ...], label: str) -> np.ndarray:
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ProcessedBoostError(f"{label} has the wrong finite shape") from exc
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ProcessedBoostError(f"{label} has the wrong finite shape")
    return np.frombuffer(
        np.ascontiguousarray(array, dtype="<f8").tobytes(), dtype="<f8"
    ).reshape(shape)


def _stored_real_metric(ell: int) -> np.ndarray:
    if type(ell) is not int or ell < 0:
        raise ProcessedBoostError("stored-real metric ell is outside its domain")
    values = np.asarray([1.0] + [2.0] * (2 * ell), dtype=np.float64)
    return _sealed(
        values,
        shape=(2 * ell + 1,),
        label="stored-real metric diagonal",
    )


def _output_metric() -> np.ndarray:
    values: list[float] = []
    for ell in range(RETAINED_LMIN, FIT_LMAX + 1):
        values.extend(_stored_real_metric(ell))
    return _sealed(
        values,
        shape=(32,),
        label="retained stored-real metric diagonal",
    )


def _scientific_registry(ell: int) -> tuple[tuple[int, int, str], ...]:
    rows: list[tuple[int, int, str]] = [(ell, 0, "REAL")]
    for m in range(1, ell + 1):
        rows.extend(((ell, m, "REAL"), (ell, m, "IMAG")))
    return tuple(rows)


def _block_metric_norm(block: object, source_ell: int) -> float:
    array = np.asarray(block, dtype=np.float64)
    width = 2 * source_ell + 1
    if array.shape != (3, 32, width) or not np.all(np.isfinite(array)):
        raise ProcessedBoostError("response block has the wrong finite shape")
    whitened = metric_whitened_matrix(
        array.reshape(96, width),
        source_metric_diagonal=_stored_real_metric(source_ell),
        output_metric_diagonal=np.tile(_output_metric(), 3),
    )
    return float(np.linalg.norm(whitened))


def _operator_norm(matrix: np.ndarray) -> float:
    singular = np.linalg.svd(matrix, compute_uv=False)
    return float(singular[0]) if singular.size else 0.0


def _mask_for(nside: int, mask_kind: str) -> np.ndarray:
    directions = healpix_sky_directions(nside)
    z = directions[:, 2]
    if mask_kind == "FULL":
        mask = np.ones(z.size, dtype=np.float64)
    elif mask_kind == "BINARY_Z":
        mask = (z >= 0.0).astype(np.float64)
    elif mask_kind == "APODIZED_Z_NARROW":
        mask = np.clip((z + 0.225) / 0.45, 0.0, 1.0)
    elif mask_kind == "APODIZED_Z_REFERENCE":
        mask = np.clip((z + 0.45) / 0.90, 0.0, 1.0)
    elif mask_kind == "APODIZED_Z_WIDE":
        mask = np.clip((z + 0.75) / 1.50, 0.0, 1.0)
    else:
        raise ProcessedBoostError("Task-7B mask kind is outside the registry")
    return _sealed(mask, shape=(z.size,), label="Task-7B mask")


def _transfer_arrays(
    processing_lmax: int,
    transfer_kind: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ell = np.arange(processing_lmax + 1, dtype=np.float64)
    if transfer_kind == "IDENTITY":
        source_beam = np.ones_like(ell)
        source_pixel = np.ones_like(ell)
        target_beam = np.ones_like(ell)
        target_pixel = np.ones_like(ell)
    elif transfer_kind == "MATCHED_GAUSSIAN":
        source_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.075**2)
        source_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.025**2)
        target_beam = source_beam.copy()
        target_pixel = source_pixel.copy()
    elif transfer_kind == "REFERENCE_GAUSSIAN":
        source_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.075**2)
        source_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.025**2)
        target_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.11**2)
        target_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.04**2)
    else:
        raise ProcessedBoostError("Task-7B transfer kind is outside the registry")
    return source_beam, source_pixel, target_beam, target_pixel


@dataclass(frozen=True)
class Task7BCaseSpec:
    case_id: str
    nside: int
    processing_lmax: int
    mask_kind: str
    transfer_kind: str
    extended_ell_max: int

    def __post_init__(self) -> None:
        hp = _healpy()
        if self.case_id not in CI_CORE_CASE_IDS:
            raise ProcessedBoostError("Task-7B case ID is outside the registry")
        if type(self.nside) is not int or not hp.isnsideok(self.nside, nest=False):
            raise ProcessedBoostError("Task-7B nside is invalid")
        if (
            type(self.processing_lmax) is not int
            or self.processing_lmax < 7
            or self.processing_lmax > 3 * self.nside - 1
        ):
            raise ProcessedBoostError("Task-7B processing lmax is invalid")
        if (
            type(self.extended_ell_max) is not int
            or not 7 <= self.extended_ell_max <= 9
            or self.processing_lmax < self.extended_ell_max + 1
        ):
            raise ProcessedBoostError(
                "Task-7B processing lmax must include the raised extended band"
            )


def _case_specs(profile: str) -> tuple[Task7BCaseSpec, ...]:
    if profile == "SMOKE":
        nside, processing_lmax, extended_max = 8, 9, 8
    elif profile == "CI_CORE":
        nside, processing_lmax, extended_max = 16, 12, 9
    else:
        raise ProcessedBoostError("Task-7B profile is outside the registry")
    definitions = (
        ("FULL_IDENTITY", "FULL", "IDENTITY"),
        ("BINARY_Z_IDENTITY", "BINARY_Z", "IDENTITY"),
        ("APODIZED_Z_NARROW_IDENTITY", "APODIZED_Z_NARROW", "IDENTITY"),
        ("APODIZED_Z_REFERENCE_IDENTITY", "APODIZED_Z_REFERENCE", "IDENTITY"),
        ("APODIZED_Z_WIDE_IDENTITY", "APODIZED_Z_WIDE", "IDENTITY"),
        (
            "APODIZED_Z_REFERENCE_MATCHED_GAUSSIAN",
            "APODIZED_Z_REFERENCE",
            "MATCHED_GAUSSIAN",
        ),
        (
            "APODIZED_Z_REFERENCE_GAUSSIAN",
            "APODIZED_Z_REFERENCE",
            "REFERENCE_GAUSSIAN",
        ),
    )
    return tuple(
        Task7BCaseSpec(
            case_id=case_id,
            nside=nside,
            processing_lmax=processing_lmax,
            mask_kind=mask_kind,
            transfer_kind=transfer_kind,
            extended_ell_max=extended_max,
        )
        for case_id, mask_kind, transfer_kind in definitions
    )


def smoke_case_spec() -> Task7BCaseSpec:
    return _case_specs("SMOKE")[3]


def _build_operator(spec: Task7BCaseSpec) -> ProcessedBoostOperator:
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


def smoke_fullsky_operator() -> ProcessedBoostOperator:
    return _build_operator(_case_specs("SMOKE")[0])


def smoke_cutsky_operator() -> ProcessedBoostOperator:
    return _build_operator(_case_specs("SMOKE")[3])


@dataclass(frozen=True)
class Task7BFullSkyReference:
    trace_by_source_ell: np.ndarray
    total_metric_frobenius_square: float
    sector_fractions: np.ndarray
    nonzero_condition_number: float


def task7b_fullsky_reference() -> Task7BFullSkyReference:
    trace = _sealed(
        np.asarray([8.0, 27.0, 91.0, 189.0, 125.0, 216.0]),
        shape=(6,),
        label="Task-7B full-sky trace sectors",
    )
    total = float(np.sum(trace))
    fractions = _sealed(
        trace / total,
        shape=(6,),
        label="Task-7B full-sky sector fractions",
    )
    return Task7BFullSkyReference(
        trace_by_source_ell=trace,
        total_metric_frobenius_square=total,
        sector_fractions=fractions,
        nonzero_condition_number=math.sqrt(63.0 / 8.0),
    )


def _mode_alm(source_ell: int, mode_index: int, processing_lmax: int) -> np.ndarray:
    hp = _healpy()
    registry = _scientific_registry(source_ell)
    if not 0 <= mode_index < len(registry):
        raise ProcessedBoostError("extended source-mode index is outside the registry")
    ell, m, component = registry[mode_index]
    alm = np.zeros(hp.Alm.getsize(processing_lmax), dtype=np.complex128)
    value = 1.0 if component == "REAL" else 1.0j
    alm[hp.Alm.getidx(processing_lmax, ell, m)] = value
    return alm


def _linear_generator_from_alm(
    alm: np.ndarray,
    operator: ProcessedBoostOperator,
    beta: np.ndarray,
) -> np.ndarray:
    hp = _healpy()
    sky_map, d_theta, d_phi_over_sin = hp.alm2map_der1(
        alm,
        nside=operator.nside,
        lmax=operator.processing_lmax,
    )
    pixels = np.arange(hp.nside2npix(operator.nside), dtype=np.int64)
    theta, phi = hp.pix2ang(operator.nside, pixels, nest=False)
    directions = healpix_sky_directions(operator.nside)
    e_theta = np.column_stack(
        (
            np.cos(theta) * np.cos(phi),
            np.cos(theta) * np.sin(phi),
            -np.sin(theta),
        )
    )
    e_phi = np.column_stack((-np.sin(phi), np.cos(phi), np.zeros_like(phi)))
    gradient = (
        np.asarray(d_theta, dtype=np.float64)[:, None] * e_theta
        + np.asarray(d_phi_over_sin, dtype=np.float64)[:, None] * e_phi
    )
    projection = directions @ beta
    tangent = beta[None, :] - projection[:, None] * directions
    generator = projection * np.asarray(sky_map, dtype=np.float64) - np.einsum(
        "ij,ij->i", tangent, gradient
    )
    if not np.all(np.isfinite(generator)):
        raise ProcessedBoostError("extended source generator became nonfinite")
    return generator


@dataclass(frozen=True)
class ExtendedSourceBlock:
    source_ell: int
    tensor: np.ndarray
    metric_whitened_matrix: np.ndarray
    metric_frobenius_norm: float
    metric_operator_norm: float
    singular_values: tuple[float, ...]
    content_id: str
    fullsky_numerical_ceiling: float = 0.25

    def __post_init__(self) -> None:
        width = 2 * self.source_ell + 1
        tensor = _sealed(
            self.tensor,
            shape=(3, 32, width),
            label="extended source response tensor",
        )
        whitened = _sealed(
            self.metric_whitened_matrix,
            shape=(96, width),
            label="extended source metric-whitened matrix",
        )
        if not self.content_id.startswith("sha256:"):
            raise ProcessedBoostError("extended source block lacks a content identity")
        object.__setattr__(self, "tensor", tensor)
        object.__setattr__(self, "metric_whitened_matrix", whitened)


def build_extended_source_block(
    operator: ProcessedBoostOperator,
    *,
    source_ell: int,
) -> ExtendedSourceBlock:
    """Build one signed first-order out-of-band source block."""

    hp = _healpy()
    if type(operator) is not ProcessedBoostOperator:
        raise ProcessedBoostError("extended source block requires a processed operator")
    if type(source_ell) is not int or not 7 <= source_ell <= 9:
        raise ProcessedBoostError("extended source ell must lie in 7..9")
    if operator.processing_lmax < source_ell + 1:
        raise ProcessedBoostError(
            "processing lmax must include the raised extended source band"
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
    whitened = metric_whitened_matrix(
        tensor.reshape(96, width),
        source_metric_diagonal=_stored_real_metric(source_ell),
        output_metric_diagonal=np.tile(_output_metric(), 3),
    )
    singular = tuple(
        float(value) for value in np.linalg.svd(whitened, compute_uv=False)
    )
    frobenius = float(np.linalg.norm(whitened))
    operator_norm = _operator_norm(whitened)
    content_id = _content_id(
        _EXTENDED_BLOCK_SCHEMA,
        {
            "source_ell": source_ell,
            "operator_id": operator.content_id,
            "map2alm_iterations": _MAP2ALM_ITERATIONS,
        },
        tensor,
        whitened,
    )
    return ExtendedSourceBlock(
        source_ell=source_ell,
        tensor=tensor,
        metric_whitened_matrix=whitened,
        metric_frobenius_norm=frobenius,
        metric_operator_norm=operator_norm,
        singular_values=singular,
        content_id=content_id,
    )


@dataclass(frozen=True)
class ExtendedTailDiagnostic:
    blocks: tuple[ExtendedSourceBlock, ...]
    cumulative_metric_frobenius: float
    cumulative_metric_operator_norm: float
    cumulative_tail_to_neighbor: float
    projection_fraction_into_registered_image: float
    minimum_principal_angle_degrees: float
    content_id: str


def _orthonormal_column_space(
    matrix: np.ndarray,
    *,
    relative_threshold: float,
) -> np.ndarray:
    u, singular, _ = np.linalg.svd(matrix, full_matrices=False)
    if singular.size == 0 or singular[0] <= 0.0:
        return np.zeros((matrix.shape[0], 0), dtype=np.float64)
    rank = int(np.count_nonzero(singular > relative_threshold * singular[0]))
    return np.asarray(u[:, :rank], dtype=np.float64)


def build_extended_tail(
    operator: ProcessedBoostOperator,
    *,
    registered_whitened_matrix: np.ndarray,
    ell6_neighbor_norm: float,
    ell_min: int = 7,
    ell_max: int = 9,
) -> ExtendedTailDiagnostic:
    if not 7 <= ell_min <= ell_max <= 9:
        raise ProcessedBoostError("extended tail ell registry is invalid")
    low = np.asarray(registered_whitened_matrix, dtype=np.float64)
    if low.shape != (96, 48) or not np.all(np.isfinite(low)):
        raise ProcessedBoostError("registered response image has the wrong shape")
    if not math.isfinite(ell6_neighbor_norm) or ell6_neighbor_norm <= 0.0:
        raise ProcessedBoostError("ell=6 physical neighbour norm must be positive")
    blocks = tuple(
        build_extended_source_block(operator, source_ell=ell)
        for ell in range(ell_min, ell_max + 1)
    )
    tail = np.concatenate(
        [block.metric_whitened_matrix for block in blocks],
        axis=1,
    )
    frobenius = float(np.linalg.norm(tail))
    operator_norm = _operator_norm(tail)
    q_low = _orthonormal_column_space(
        low,
        relative_threshold=_RANK_RELATIVE_THRESHOLD,
    )
    q_tail = _orthonormal_column_space(
        tail,
        relative_threshold=_RANK_RELATIVE_THRESHOLD,
    )
    if frobenius <= np.finfo(float).tiny or q_tail.shape[1] == 0:
        projection_fraction = 0.0
        angle = 90.0
    else:
        projected = q_low.T @ tail
        projection_fraction = float(
            np.linalg.norm(projected) ** 2
            / max(frobenius * frobenius, np.finfo(float).tiny)
        )
        overlap = q_low.T @ q_tail
        principal_cosine = min(1.0, max(0.0, _operator_norm(overlap)))
        angle = math.degrees(math.acos(principal_cosine))
    projection_fraction = min(1.0, max(0.0, projection_fraction))
    content_id = _content_id(
        _EXTENDED_TAIL_SCHEMA,
        {
            "operator_id": operator.content_id,
            "ell_min": ell_min,
            "ell_max": ell_max,
            "block_ids": [block.content_id for block in blocks],
            "ell6_neighbor_norm_hex": float(ell6_neighbor_norm).hex(),
            "projection_fraction_hex": projection_fraction.hex(),
            "minimum_principal_angle_degrees_hex": float(angle).hex(),
        },
        tail,
    )
    return ExtendedTailDiagnostic(
        blocks=blocks,
        cumulative_metric_frobenius=frobenius,
        cumulative_metric_operator_norm=operator_norm,
        cumulative_tail_to_neighbor=frobenius / ell6_neighbor_norm,
        projection_fraction_into_registered_image=projection_fraction,
        minimum_principal_angle_degrees=float(angle),
        content_id=content_id,
    )


@dataclass(frozen=True)
class Task7BCaseResult:
    case_id: str
    nside: int
    processing_lmax: int
    mask_kind: str
    transfer_kind: str
    operator_id: str
    jacobian_id: str
    jacobian_rank: int
    jacobian_nonzero_condition: float
    joint_normal_condition: float
    f_sky_mean: float
    f_sky_quadratic: float
    f_sky_effective: float
    transition_fraction: float
    source_sector_frobenius_fractions: tuple[float, ...]
    weak_mode_sector_weights: tuple[float, ...]
    weakest_nonzero_singular_value: float
    ell6_neighbor_norm: float
    ell6_alias_norm: float
    ell6_alias_to_neighbor: float
    monopole_replay_relative: float
    tail: ExtendedTailDiagnostic
    candidate: bool
    content_id: str

    def scalar_record(self) -> dict[str, object]:
        return {
            "schema": _CASE_SCHEMA,
            "case_id": self.case_id,
            "nside": self.nside,
            "processing_lmax": self.processing_lmax,
            "mask_kind": self.mask_kind,
            "transfer_kind": self.transfer_kind,
            "operator_id": self.operator_id,
            "jacobian_id": self.jacobian_id,
            "jacobian_rank": self.jacobian_rank,
            "jacobian_nonzero_condition": self.jacobian_nonzero_condition,
            "joint_normal_condition": self.joint_normal_condition,
            "f_sky_mean": self.f_sky_mean,
            "f_sky_quadratic": self.f_sky_quadratic,
            "f_sky_effective": self.f_sky_effective,
            "transition_fraction": self.transition_fraction,
            "source_sector_frobenius_fractions": list(
                self.source_sector_frobenius_fractions
            ),
            "weak_mode_sector_weights": list(self.weak_mode_sector_weights),
            "weakest_nonzero_singular_value": self.weakest_nonzero_singular_value,
            "ell6_neighbor_norm": self.ell6_neighbor_norm,
            "ell6_alias_norm": self.ell6_alias_norm,
            "ell6_alias_to_neighbor": self.ell6_alias_to_neighbor,
            "monopole_replay_relative": self.monopole_replay_relative,
            "extended_tail": {
                "content_id": self.tail.content_id,
                "cumulative_metric_frobenius": (
                    self.tail.cumulative_metric_frobenius
                ),
                "cumulative_metric_operator_norm": (
                    self.tail.cumulative_metric_operator_norm
                ),
                "cumulative_tail_to_neighbor": (
                    self.tail.cumulative_tail_to_neighbor
                ),
                "projection_fraction_into_registered_image": (
                    self.tail.projection_fraction_into_registered_image
                ),
                "minimum_principal_angle_degrees": (
                    self.tail.minimum_principal_angle_degrees
                ),
                "blocks": [
                    {
                        "source_ell": block.source_ell,
                        "metric_frobenius_norm": block.metric_frobenius_norm,
                        "metric_operator_norm": block.metric_operator_norm,
                        "content_id": block.content_id,
                    }
                    for block in self.tail.blocks
                ],
            },
            "candidate": self.candidate,
            "content_id": self.content_id,
        }


def _sector_diagnostics(
    registered_whitened: np.ndarray,
) -> tuple[tuple[float, ...], tuple[float, ...], float]:
    matrix = np.asarray(registered_whitened, dtype=np.float64)
    if matrix.shape != (96, 49) or not np.all(np.isfinite(matrix)):
        raise ProcessedBoostError(
            "registered metric-whitened Jacobian has the wrong shape"
        )
    anisotropy = matrix[:, 1:]
    _, singular, vh = np.linalg.svd(anisotropy, full_matrices=False)
    if singular.size != 48 or singular[0] <= 0.0:
        raise ProcessedBoostError("registered anisotropy SVD failed")
    rank = int(
        np.count_nonzero(singular > _RANK_RELATIVE_THRESHOLD * singular[0])
    )
    if rank != 48:
        raise ProcessedBoostError("registered anisotropy response lost rank")
    total_square = float(np.linalg.norm(anisotropy) ** 2)
    fractions: list[float] = []
    weights: list[float] = []
    weak = vh[-1]
    cursor = 0
    for ell in range(1, 7):
        width = 2 * ell + 1
        block = anisotropy[:, cursor : cursor + width]
        weak_block = weak[cursor : cursor + width]
        fractions.append(float(np.linalg.norm(block) ** 2 / total_square))
        weights.append(float(np.dot(weak_block, weak_block)))
        cursor += width
    if cursor != 48:
        raise ProcessedBoostError("source-sector registry drifted")
    if (
        abs(sum(fractions) - 1.0) > _SECTOR_SUM_ATOL
        or abs(sum(weights) - 1.0) > _SECTOR_SUM_ATOL
    ):
        raise ProcessedBoostError("source-sector diagnostics are not normalized")
    return tuple(fractions), tuple(weights), float(singular[-1])


def build_task7b_case(spec: Task7BCaseSpec) -> Task7BCaseResult:
    if type(spec) is not Task7BCaseSpec:
        raise ProcessedBoostError(
            "Task-7B case requires an exact case specification"
        )
    operator = _build_operator(spec)
    jacobian = build_processed_boost_jacobian(operator)
    fractions, weak_weights, weakest = _sector_diagnostics(
        jacobian.metric_whitened_stacked_matrix
    )
    neighbor_norm = _block_metric_norm(
        jacobian.ell6_expected_neighbor_l5_block,
        source_ell=6,
    )
    alias_norm = _block_metric_norm(
        jacobian.ell6_cutsky_alias_residual,
        source_ell=6,
    )
    tail = build_extended_tail(
        operator,
        registered_whitened_matrix=jacobian.metric_whitened_stacked_matrix[:, 1:],
        ell6_neighbor_norm=neighbor_norm,
        ell_min=7,
        ell_max=spec.extended_ell_max,
    )
    mask = np.asarray(operator.mask, dtype=np.float64)
    mean = float(np.mean(mask))
    quadratic = float(np.mean(mask * mask))
    effective = mean * mean / quadratic
    transition = float(np.mean((mask > 0.0) & (mask < 1.0)))
    alias_ratio = alias_norm / neighbor_norm
    candidate = bool(
        spec.mask_kind != "FULL"
        and jacobian.metric_whitened_rank == 48
        and jacobian.metric_whitened_nonzero_condition_number
        <= _CANDIDATE_CONDITION_CEILING
        and alias_ratio <= _CANDIDATE_ALIAS_RATIO_CEILING
        and tail.cumulative_tail_to_neighbor <= _CANDIDATE_TAIL_RATIO_CEILING
    )
    scalar_payload = {
        "case_id": spec.case_id,
        "nside": spec.nside,
        "processing_lmax": spec.processing_lmax,
        "mask_kind": spec.mask_kind,
        "transfer_kind": spec.transfer_kind,
        "operator_id": operator.content_id,
        "jacobian_id": jacobian.content_id,
        "tail_id": tail.content_id,
        "candidate": candidate,
    }
    content_id = _content_id(_CASE_SCHEMA, scalar_payload)
    return Task7BCaseResult(
        case_id=spec.case_id,
        nside=spec.nside,
        processing_lmax=spec.processing_lmax,
        mask_kind=spec.mask_kind,
        transfer_kind=spec.transfer_kind,
        operator_id=operator.content_id,
        jacobian_id=jacobian.content_id,
        jacobian_rank=jacobian.metric_whitened_rank,
        jacobian_nonzero_condition=(
            jacobian.metric_whitened_nonzero_condition_number
        ),
        joint_normal_condition=operator.joint_operator.condition_number,
        f_sky_mean=mean,
        f_sky_quadratic=quadratic,
        f_sky_effective=effective,
        transition_fraction=transition,
        source_sector_frobenius_fractions=fractions,
        weak_mode_sector_weights=weak_weights,
        weakest_nonzero_singular_value=weakest,
        ell6_neighbor_norm=neighbor_norm,
        ell6_alias_norm=alias_norm,
        ell6_alias_to_neighbor=alias_ratio,
        monopole_replay_relative=(
            jacobian.monopole_relative_to_nonmonopole_max
        ),
        tail=tail,
        candidate=candidate,
        content_id=content_id,
    )


@dataclass(frozen=True)
class Task7BAtlas:
    source_revision: str
    profile: str
    cases: tuple[Task7BCaseResult, ...]
    candidate_case_ids: tuple[str, ...]
    terminal: Task7BTerminal
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        if _REVISION_RE.fullmatch(self.source_revision) is None:
            raise ProcessedBoostError(
                "Task-7B source revision must be a 40-hex identity"
            )
        if self.profile not in {"SMOKE", "CI_CORE"}:
            raise ProcessedBoostError("Task-7B profile is outside the registry")
        if tuple(case.case_id for case in self.cases) != CI_CORE_CASE_IDS:
            raise ProcessedBoostError("Task-7B case order drifted")
        expected_candidates = tuple(
            case.case_id for case in self.cases if case.candidate
        )
        if self.candidate_case_ids != expected_candidates:
            raise ProcessedBoostError("Task-7B candidate registry drifted")
        expected_terminal = (
            Task7BTerminal.PASS_TASK7B_ATLAS_CANDIDATE_FOUND
            if expected_candidates
            else Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE
        )
        if self.terminal is not expected_terminal:
            raise ProcessedBoostError("Task-7B terminal differs from its cases")
        content_id = _content_id(
            _IDENTIFIABILITY_SCHEMA,
            self.scalar_record(include_content_id=False),
        )
        object.__setattr__(self, "content_id", content_id)

    def scalar_record(self, *, include_content_id: bool = True) -> dict[str, object]:
        record: dict[str, object] = {
            "schema": _IDENTIFIABILITY_SCHEMA,
            "source_revision": self.source_revision,
            "profile": self.profile,
            "terminal": self.terminal.value,
            "candidate_case_ids": list(self.candidate_case_ids),
            "candidate_thresholds": {
                "rank": 48,
                "metric_whitened_nonzero_condition_ceiling": (
                    _CANDIDATE_CONDITION_CEILING
                ),
                "ell6_alias_to_neighbor_ceiling": (
                    _CANDIDATE_ALIAS_RATIO_CEILING
                ),
                "ell7_to_ell9_tail_to_neighbor_ceiling": (
                    _CANDIDATE_TAIL_RATIO_CEILING
                ),
                "semantics": (
                    "ENGINEERING_PREREGISTRATION_NOT_INFERENCE_THEOREM"
                ),
            },
            "fullsky_reference": {
                "trace_by_source_ell": [8, 27, 91, 189, 125, 216],
                "total_metric_frobenius_square": 656,
                "sector_fractions": [
                    1.0 / 82.0,
                    27.0 / 656.0,
                    91.0 / 656.0,
                    189.0 / 656.0,
                    125.0 / 656.0,
                    27.0 / 82.0,
                ],
                "nonzero_condition_number": math.sqrt(63.0 / 8.0),
            },
            "cases": [case.scalar_record() for case in self.cases],
            "claim_boundary": {
                "synthetic_processed_local_observer_scalar_response": True,
                "raw_planck_absolute_temperature_admitted": False,
                "observed_rank": False,
                "empirical_beta": False,
                "boost_subtraction": False,
                "global_tilt": False,
                "polarization_result": False,
                "foreground_exclusion": False,
                "bianchi_attribution": False,
                "formal_P01_P27_replay": False,
                "merge_authorized": False,
            },
        }
        if include_content_id:
            record["content_id"] = self.content_id
        return record


def build_task7b_atlas(
    *,
    source_revision: str,
    profile: str = "CI_CORE",
) -> Task7BAtlas:
    if _REVISION_RE.fullmatch(source_revision) is None:
        raise ProcessedBoostError(
            "Task-7B source revision must be a 40-hex identity"
        )
    specs = _case_specs(profile)
    cases = tuple(build_task7b_case(spec) for spec in specs)
    candidates = tuple(case.case_id for case in cases if case.candidate)
    terminal = (
        Task7BTerminal.PASS_TASK7B_ATLAS_CANDIDATE_FOUND
        if candidates
        else Task7BTerminal.PASS_TASK7B_ATLAS_NO_CANDIDATE
    )
    return Task7BAtlas(
        source_revision=source_revision,
        profile=profile,
        cases=cases,
        candidate_case_ids=candidates,
        terminal=terminal,
    )


@dataclass(frozen=True)
class Task7BArtifactBundle:
    output_dir: Path
    file_sha256: dict[str, str]
    manifest_sha256: str


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="ascii",
    )


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ProcessedBoostError("Task-7B CSV table may not be empty")
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_plots(atlas: Task7BAtlas, output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    metadata = {"Software": "htt_base WU011 Task7B"}
    labels = [case.case_id for case in atlas.cases]
    x = np.arange(len(labels))
    floor = np.finfo(float).tiny

    plt.figure(figsize=(9.0, 4.8))
    plt.plot(
        x,
        [case.jacobian_nonzero_condition for case in atlas.cases],
        marker="o",
        label="Response condition",
    )
    plt.plot(
        x,
        [case.joint_normal_condition for case in atlas.cases],
        marker="s",
        label="Joint normal condition",
    )
    plt.axhline(_CANDIDATE_CONDITION_CEILING, linestyle="--")
    plt.yscale("log")
    plt.xticks(x, labels, rotation=32, ha="right")
    plt.ylabel("Condition number")
    plt.title("WU-011 Task-7B conditioning by processed case")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output / "condition_vs_mask.png", dpi=180, metadata=metadata)
    plt.close()

    plt.figure(figsize=(9.0, 4.8))
    plt.plot(
        x,
        [max(case.ell6_alias_to_neighbor, floor) for case in atlas.cases],
        marker="o",
        label="ell=7 alias / ell=6->5 neighbour",
    )
    plt.plot(
        x,
        [max(case.tail.cumulative_tail_to_neighbor, floor) for case in atlas.cases],
        marker="s",
        label="ell>=7 tail / ell=6->5 neighbour",
    )
    plt.axhline(1.0, linestyle="--")
    plt.yscale("log")
    plt.xticks(x, labels, rotation=32, ha="right")
    plt.ylabel("Dimensionless response ratio")
    plt.title("WU-011 Task-7B physical-neighbour and leakage ratios")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output / "alias_and_tail_vs_case.png", dpi=180, metadata=metadata)
    plt.close()

    sector_ells = np.arange(1, 7)
    plt.figure(figsize=(7.2, 4.8))
    for case in atlas.cases:
        plt.plot(
            sector_ells,
            case.weak_mode_sector_weights,
            marker="o",
            label=case.case_id,
        )
    plt.xticks(sector_ells)
    plt.xlabel("Source multipole ell")
    plt.ylabel("Weakest right-singular-vector sector weight")
    plt.title("WU-011 weak-response source sectors")
    plt.legend(fontsize=6)
    plt.tight_layout()
    plt.savefig(
        output / "weak_mode_sector_weights.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()

    plt.figure(figsize=(7.2, 4.8))
    for case in atlas.cases:
        plt.plot(
            sector_ells,
            case.source_sector_frobenius_fractions,
            marker="o",
            label=case.case_id,
        )
    plt.xticks(sector_ells)
    plt.xlabel("Source multipole ell")
    plt.ylabel("Metric Frobenius fraction")
    plt.title("WU-011 source-sector response power")
    plt.legend(fontsize=6)
    plt.tight_layout()
    plt.savefig(
        output / "source_sector_frobenius_fractions.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()

    plt.figure(figsize=(7.2, 4.8))
    for case in atlas.cases:
        plt.plot(
            [block.source_ell for block in case.tail.blocks],
            [
                max(block.metric_frobenius_norm, floor)
                for block in case.tail.blocks
            ],
            marker="o",
            label=case.case_id,
        )
    plt.yscale("log")
    plt.xlabel("Extended source multipole ell")
    plt.ylabel("Metric-whitened block Frobenius norm")
    plt.title("WU-011 out-of-band leakage by source multipole")
    plt.legend(fontsize=6)
    plt.tight_layout()
    plt.savefig(
        output / "extended_leakage_decay.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()


def write_task7b_artifacts(
    atlas: Task7BAtlas,
    output_dir: Path,
) -> Task7BArtifactBundle:
    if type(atlas) is not Task7BAtlas:
        raise ProcessedBoostError(
            "Task-7B artifact writer requires an exact atlas"
        )
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise ProcessedBoostError(
            "Task-7B output directory must be absent or empty"
        )
    output.mkdir(parents=True, exist_ok=True)

    terminal = {
        "schema": _TERMINAL_SCHEMA,
        "terminal": atlas.terminal.value,
        "source_revision": atlas.source_revision,
        "profile": atlas.profile,
        "atlas_content_id": atlas.content_id,
        "candidate_case_ids": list(atlas.candidate_case_ids),
        "claim_promotion": False,
        "merge_authorized": False,
    }
    _write_json(output / "terminal.json", terminal)
    _write_json(output / "summary.json", atlas.scalar_record())
    _write_csv(
        output / "cases.csv",
        [
            {
                "case_id": case.case_id,
                "mask_kind": case.mask_kind,
                "transfer_kind": case.transfer_kind,
                "f_sky_mean": case.f_sky_mean,
                "f_sky_quadratic": case.f_sky_quadratic,
                "f_sky_effective": case.f_sky_effective,
                "transition_fraction": case.transition_fraction,
                "joint_normal_condition": case.joint_normal_condition,
                "jacobian_nonzero_condition": case.jacobian_nonzero_condition,
                "weakest_nonzero_singular_value": (
                    case.weakest_nonzero_singular_value
                ),
                "ell6_neighbor_norm": case.ell6_neighbor_norm,
                "ell6_alias_norm": case.ell6_alias_norm,
                "ell6_alias_to_neighbor": case.ell6_alias_to_neighbor,
                "extended_tail_to_neighbor": (
                    case.tail.cumulative_tail_to_neighbor
                ),
                "tail_projection_fraction": (
                    case.tail.projection_fraction_into_registered_image
                ),
                "minimum_principal_angle_degrees": (
                    case.tail.minimum_principal_angle_degrees
                ),
                "candidate": case.candidate,
                "content_id": case.content_id,
            }
            for case in atlas.cases
        ],
    )
    sector_rows: list[dict[str, object]] = []
    for case in atlas.cases:
        for ell, (fraction, weak_weight) in enumerate(
            zip(
                case.source_sector_frobenius_fractions,
                case.weak_mode_sector_weights,
            ),
            start=1,
        ):
            sector_rows.append(
                {
                    "case_id": case.case_id,
                    "source_ell": ell,
                    "frobenius_fraction": fraction,
                    "weak_mode_weight": weak_weight,
                }
            )
    _write_csv(output / "sector_participation.csv", sector_rows)

    extended_rows: list[dict[str, object]] = []
    for case in atlas.cases:
        for block in case.tail.blocks:
            extended_rows.append(
                {
                    "case_id": case.case_id,
                    "source_ell": block.source_ell,
                    "metric_frobenius_norm": block.metric_frobenius_norm,
                    "metric_operator_norm": block.metric_operator_norm,
                    "cumulative_tail_to_neighbor": (
                        case.tail.cumulative_tail_to_neighbor
                    ),
                    "projection_fraction_into_registered_image": (
                        case.tail.projection_fraction_into_registered_image
                    ),
                    "minimum_principal_angle_degrees": (
                        case.tail.minimum_principal_angle_degrees
                    ),
                    "content_id": block.content_id,
                }
            )
    _write_csv(output / "extended_source_leakage.csv", extended_rows)
    _write_csv(
        output / "gate_ratios.csv",
        [
            {
                "case_id": case.case_id,
                "condition_ratio_to_ceiling": (
                    case.jacobian_nonzero_condition
                    / _CANDIDATE_CONDITION_CEILING
                ),
                "ell6_alias_ratio_to_ceiling": (
                    case.ell6_alias_to_neighbor
                    / _CANDIDATE_ALIAS_RATIO_CEILING
                ),
                "extended_tail_ratio_to_ceiling": (
                    case.tail.cumulative_tail_to_neighbor
                    / _CANDIDATE_TAIL_RATIO_CEILING
                ),
                "candidate": case.candidate,
            }
            for case in atlas.cases
        ],
    )
    _write_plots(atlas, output)

    files = sorted(path for path in output.iterdir() if path.is_file())
    hashes = {path.name: _file_sha256(path) for path in files}
    manifest = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(hashes.items())
    )
    (output / "SHA256SUMS").write_text(manifest, encoding="ascii")
    return Task7BArtifactBundle(
        output_dir=output,
        file_sha256=hashes,
        manifest_sha256=_file_sha256(output / "SHA256SUMS"),
    )


def verify_task7b_artifacts(output_dir: Path) -> dict[str, object]:
    output = Path(output_dir)
    manifest_path = output / "SHA256SUMS"
    if (
        not output.is_dir()
        or not manifest_path.is_file()
        or manifest_path.is_symlink()
    ):
        raise ProcessedBoostError(
            "Task-7B artifact manifest is missing or unsafe"
        )
    entries: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="ascii").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or re.fullmatch(r"[0-9a-f]{64}", parts[0]) is None:
            raise ProcessedBoostError("Task-7B artifact manifest is malformed")
        digest, name = parts
        if Path(name).name != name or name in entries:
            raise ProcessedBoostError("Task-7B artifact manifest path is unsafe")
        path = output / name
        if (
            not path.is_file()
            or path.is_symlink()
            or _file_sha256(path) != digest
        ):
            raise ProcessedBoostError(
                "Task-7B artifact hash verification failed"
            )
        entries[name] = digest
    required = {
        "terminal.json",
        "summary.json",
        "cases.csv",
        "sector_participation.csv",
        "extended_source_leakage.csv",
        "gate_ratios.csv",
        "condition_vs_mask.png",
        "alias_and_tail_vs_case.png",
        "weak_mode_sector_weights.png",
        "source_sector_frobenius_fractions.png",
        "extended_leakage_decay.png",
    }
    if not required.issubset(entries):
        raise ProcessedBoostError("Task-7B artifact set is incomplete")
    terminal = json.loads(
        (output / "terminal.json").read_text(encoding="ascii")
    )
    summary = json.loads((output / "summary.json").read_text(encoding="ascii"))
    if (
        terminal.get("schema") != _TERMINAL_SCHEMA
        or summary.get("schema") != _IDENTIFIABILITY_SCHEMA
        or terminal.get("terminal") != summary.get("terminal")
        or terminal.get("source_revision") != summary.get("source_revision")
        or terminal.get("profile") != summary.get("profile")
        or terminal.get("atlas_content_id") != summary.get("content_id")
        or terminal.get("candidate_case_ids")
        != summary.get("candidate_case_ids")
        or terminal.get("claim_promotion") is not False
        or terminal.get("merge_authorized") is not False
    ):
        raise ProcessedBoostError(
            "Task-7B terminal and summary binding differs"
        )
    return {
        "schema": _ARTIFACT_SCHEMA,
        "terminal": terminal["terminal"],
        "source_revision": terminal["source_revision"],
        "profile": terminal["profile"],
        "atlas_content_id": terminal["atlas_content_id"],
        "candidate_case_ids": terminal["candidate_case_ids"],
        "manifest_entries": len(entries),
        "manifest_sha256": _file_sha256(manifest_path),
    }


__all__ = [
    "CI_CORE_CASE_IDS",
    "ExtendedSourceBlock",
    "ExtendedTailDiagnostic",
    "Task7BArtifactBundle",
    "Task7BAtlas",
    "Task7BCaseResult",
    "Task7BCaseSpec",
    "Task7BFullSkyReference",
    "Task7BTerminal",
    "build_extended_source_block",
    "build_extended_tail",
    "build_task7b_atlas",
    "build_task7b_case",
    "smoke_case_spec",
    "smoke_cutsky_operator",
    "smoke_fullsky_operator",
    "task7b_fullsky_reference",
    "verify_task7b_artifacts",
    "write_task7b_artifacts",
]

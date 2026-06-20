"""Joint rest-frame identifiability diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math
import re
from typing import Any

import numpy as np

from .cross_survey_covariance import (
    covariance_inverse_sqrt,
    validate_positive_definite_covariance,
)

__all__ = [
    "JointRestFrameRankAudit",
    "RestFrameResponseBlocks",
    "evaluate_joint_rest_frame_rank_gate",
]


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _text(value: object, field: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _sha256_text(value: object, field: str) -> str:
    text = _text(value, field)
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{field} must be a sha256 hash")
    return text


def _sha256_sequence(value: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{field} must be a non-empty sequence of sha256 hashes")
    return tuple(_sha256_text(item, field) for item in value)


def _matrix(value: object, field: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim == 1:
        array = array[:, None]
    if array.ndim != 2:
        raise ValueError(f"{field} must be one- or two-dimensional")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must contain finite values")
    return array


def _optional_matrix(value: object, field: str, *, rows: int) -> np.ndarray:
    if value is None:
        return np.zeros((rows, 0), dtype=float)
    array = _matrix(value, field)
    if array.shape[0] != rows:
        raise ValueError(f"{field} row count must match response row count")
    return array


def _vector(value: object, field: str, *, rows: int) -> np.ndarray:
    if value is None:
        return np.zeros(rows, dtype=float)
    array = np.asarray(value, dtype=float)
    if array.shape != (rows,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must be a finite vector with response row count")
    return array


def _labels(value: Sequence[str], *, rows: int) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("channel_labels must be a sequence")
    result = tuple(_text(item, "channel_labels") for item in value)
    if len(result) != rows:
        raise ValueError("channel_labels length must match response row count")
    if len(set(result)) != len(result):
        raise ValueError("channel_labels must be unique")
    return result


def _nuisance_projector(nuisance_white: np.ndarray, tolerance: float) -> np.ndarray:
    if nuisance_white.shape[1] == 0:
        return np.eye(nuisance_white.shape[0])
    u, singular_values, _ = np.linalg.svd(nuisance_white, full_matrices=False)
    if singular_values.size == 0:
        return np.eye(nuisance_white.shape[0])
    threshold = tolerance * max(float(singular_values[0]), 1.0)
    rank = int(np.sum(singular_values > threshold))
    if rank == 0:
        return np.eye(nuisance_white.shape[0])
    basis = u[:, :rank]
    return np.eye(nuisance_white.shape[0]) - basis @ basis.T


def _rank_from_projected(projected: np.ndarray, tolerance: float) -> tuple[int, tuple[float, ...], float, float]:
    singular_values = np.linalg.svd(projected, compute_uv=False)
    if singular_values.size == 0:
        return 0, (), tolerance, float("inf")
    threshold = tolerance * max(float(singular_values[0]), 1.0)
    rank = int(np.sum(singular_values > threshold))
    if float(singular_values[-1]) > threshold:
        condition = float(singular_values[0] / singular_values[-1])
    else:
        condition = float("inf")
    return rank, tuple(float(value) for value in singular_values), threshold, condition


@dataclass(frozen=True)
class RestFrameResponseBlocks:
    """Response blocks for pre-inference joint rest-frame identifiability."""

    observer_cmb_boost_response: object
    local_flow_basis_response: object
    global_rest_frame_offset_response: object
    survey_systematic_response: object
    covariance: object
    channel_labels: Sequence[str]
    config_hash: str
    input_hashes: Sequence[str]
    generating_command: str
    worktree_state: str
    survey_axis_vector: object | None = None
    survey_axis_frame: str = "response_channel_space"
    survey_axis_provenance: str = "not_bound"
    sky_support_status: str = "not_bound"
    mask_status: str = "not_bound"
    covariance_status: str = "supplied_positive_definite"
    null_mock_status: str = "not_bound"

    def __post_init__(self) -> None:
        observer = _matrix(self.observer_cmb_boost_response, "observer_cmb_boost_response")
        rows = observer.shape[0]
        local = _optional_matrix(self.local_flow_basis_response, "local_flow_basis_response", rows=rows)
        global_response = _optional_matrix(
            self.global_rest_frame_offset_response,
            "global_rest_frame_offset_response",
            rows=rows,
        )
        systematic = _optional_matrix(
            self.survey_systematic_response,
            "survey_systematic_response",
            rows=rows,
        )
        if global_response.shape[1] <= 0:
            raise ValueError("global_rest_frame_offset_response must contain at least one column")
        covariance = validate_positive_definite_covariance(self.covariance, rows=rows)
        object.__setattr__(self, "observer_cmb_boost_response", observer)
        object.__setattr__(self, "local_flow_basis_response", local)
        object.__setattr__(self, "global_rest_frame_offset_response", global_response)
        object.__setattr__(self, "survey_systematic_response", systematic)
        object.__setattr__(self, "covariance", covariance)
        object.__setattr__(self, "channel_labels", _labels(self.channel_labels, rows=rows))
        object.__setattr__(self, "survey_axis_vector", _vector(self.survey_axis_vector, "survey_axis_vector", rows=rows))
        object.__setattr__(self, "config_hash", _sha256_text(self.config_hash, "config_hash"))
        object.__setattr__(
            self,
            "input_hashes",
            _sha256_sequence(tuple(self.input_hashes), "input_hashes"),
        )
        object.__setattr__(
            self,
            "generating_command",
            _text(self.generating_command, "generating_command"),
        )
        object.__setattr__(self, "worktree_state", _text(self.worktree_state, "worktree_state"))
        object.__setattr__(self, "survey_axis_frame", _text(self.survey_axis_frame, "survey_axis_frame"))
        object.__setattr__(
            self,
            "survey_axis_provenance",
            _text(self.survey_axis_provenance, "survey_axis_provenance"),
        )
        object.__setattr__(self, "sky_support_status", _text(self.sky_support_status, "sky_support_status"))
        object.__setattr__(self, "mask_status", _text(self.mask_status, "mask_status"))
        object.__setattr__(self, "covariance_status", _text(self.covariance_status, "covariance_status"))
        object.__setattr__(self, "null_mock_status", _text(self.null_mock_status, "null_mock_status"))

    @property
    def nuisance_response(self) -> np.ndarray:
        return np.column_stack(
            (
                self.observer_cmb_boost_response,
                self.local_flow_basis_response,
                self.survey_systematic_response,
            )
        )

    @property
    def row_count(self) -> int:
        return int(self.global_rest_frame_offset_response.shape[0])

    @property
    def target_dimension(self) -> int:
        return int(self.global_rest_frame_offset_response.shape[1])


@dataclass(frozen=True)
class JointRestFrameRankAudit:
    """Diagnostic rank gate for joint rest-frame response blocks."""

    blocks: RestFrameResponseBlocks
    projected_rank: int
    singular_values: tuple[float, ...]
    rank_tolerance: float
    rank_threshold: float
    condition_number: float
    channel_ablation_stability: dict[str, Any]
    survey_axis_overlap: dict[str, Any]
    no_claim_reasons: tuple[str, ...]

    @property
    def target_dimension(self) -> int:
        return self.blocks.target_dimension

    @property
    def full_rank(self) -> bool:
        return self.projected_rank == self.target_dimension

    @property
    def rank_status(self) -> str:
        return "full_rank_candidate" if self.full_rank else "rank_deficient_no_claim"

    @property
    def claim_status(self) -> str:
        return "pre_inference_rank_candidate" if self.full_rank else "no_claim_rank_deficient"

    def to_payload(self) -> dict[str, Any]:
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "claim_tier": "diagnostic_only",
            "artifact_role": "joint_rest_frame_rank_gate",
            "production_status": "pre_inference_gate",
            "transfer_source": "none",
            "native_solver_result": False,
            "family_identification": False,
            "target_dimension": self.target_dimension,
            "projected_rank": self.projected_rank,
            "singular_values": list(self.singular_values),
            "rank_tolerance": self.rank_tolerance,
            "rank_threshold": self.rank_threshold,
            "condition_number": self.condition_number,
            "full_rank": self.full_rank,
            "rank_status": self.rank_status,
            "claim_status": self.claim_status,
            "channel_ablation_stability": dict(self.channel_ablation_stability),
            "survey_axis_overlap": dict(self.survey_axis_overlap),
            "survey_axis_metadata": {
                "axis_vector": [float(value) for value in self.blocks.survey_axis_vector],
                "axis_frame": self.blocks.survey_axis_frame,
                "axis_provenance": self.blocks.survey_axis_provenance,
                "sky_support_status": self.blocks.sky_support_status,
                "mask_status": self.blocks.mask_status,
                "covariance_status": self.blocks.covariance_status,
                "null_mock_status": self.blocks.null_mock_status,
            },
            "no_claim_reasons": list(self.no_claim_reasons),
            "config_hash": self.blocks.config_hash,
            "input_hashes": list(self.blocks.input_hashes),
            "generating_command": self.blocks.generating_command,
            "git_commit_or_worktree_state": self.blocks.worktree_state,
            "caveats": [
                "pre-inference diagnostic rank gate only",
                "matched nulls, PPC, LOOCV, and covariance sensitivity remain separate gates",
                "not evidence-grade output",
                "not native solver validation",
                "not family or geometry identification",
            ],
        }


def _projected_global_response(blocks: RestFrameResponseBlocks, *, row_mask: np.ndarray | None = None) -> np.ndarray:
    if row_mask is None:
        covariance = blocks.covariance
        target = blocks.global_rest_frame_offset_response
        nuisance = blocks.nuisance_response
    else:
        covariance = blocks.covariance[np.ix_(row_mask, row_mask)]
        target = blocks.global_rest_frame_offset_response[row_mask, :]
        nuisance = blocks.nuisance_response[row_mask, :]
    whitening = covariance_inverse_sqrt(covariance)
    nuisance_white = whitening @ nuisance
    projector = _nuisance_projector(nuisance_white, 1.0e-10)
    return projector @ whitening @ target


def _channel_ablation(blocks: RestFrameResponseBlocks) -> dict[str, Any]:
    statuses: dict[str, str] = {}
    for index, label in enumerate(blocks.channel_labels):
        if blocks.row_count <= 1:
            statuses[label] = "not_evaluated_single_channel_model"
            continue
        mask = np.ones(blocks.row_count, dtype=bool)
        mask[index] = False
        try:
            projected = _projected_global_response(blocks, row_mask=mask)
            rank, _, _, _ = _rank_from_projected(projected, 1.0e-10)
        except ValueError:
            statuses[label] = "invalid_after_ablation"
            continue
        statuses[label] = "full_rank" if rank == blocks.target_dimension else "rank_deficient"
    return {
        "all_single_channel_ablations_full_rank": all(status == "full_rank" for status in statuses.values()),
        "per_channel_status": statuses,
    }


def _survey_axis_overlap(blocks: RestFrameResponseBlocks, projected: np.ndarray) -> dict[str, Any]:
    axis = np.asarray(blocks.survey_axis_vector, dtype=float)
    norm = float(np.linalg.norm(axis))
    if norm == 0.0:
        return {
            "status": "zero_norm_axis",
            "max_abs_cosine": 0.0,
            "axis_norm": 0.0,
            "whitened_axis_norm": 0.0,
        }
    whitening = covariance_inverse_sqrt(blocks.covariance)
    axis_white = whitening @ axis
    axis_white_norm = float(np.linalg.norm(axis_white))
    if axis_white_norm == 0.0:
        return {
            "status": "zero_norm_axis",
            "max_abs_cosine": 0.0,
            "axis_norm": norm,
            "whitened_axis_norm": 0.0,
        }
    column_norms = np.linalg.norm(projected, axis=0)
    overlaps = []
    for col, col_norm in zip(projected.T, column_norms, strict=True):
        if col_norm == 0.0:
            overlaps.append(0.0)
        else:
            overlaps.append(abs(float(np.dot(axis_white, col) / (axis_white_norm * col_norm))))
    return {
        "status": "finite",
        "max_abs_cosine": float(max(overlaps) if overlaps else 0.0),
        "axis_norm": norm,
        "whitened_axis_norm": axis_white_norm,
    }


def evaluate_joint_rest_frame_rank_gate(blocks: RestFrameResponseBlocks) -> JointRestFrameRankAudit:
    """Evaluate the pre-inference nuisance-projected global response rank."""

    projected = _projected_global_response(blocks)
    rank_tolerance = 1.0e-10
    rank, singular_values, threshold, condition = _rank_from_projected(projected, rank_tolerance)
    reasons: list[str] = []
    if rank != blocks.target_dimension:
        reasons.append("rank_deficient_after_nuisance_projection")
    if not math.isfinite(condition):
        reasons.append("ill_conditioned_projected_response")
    return JointRestFrameRankAudit(
        blocks=blocks,
        projected_rank=rank,
        singular_values=singular_values,
        rank_tolerance=rank_tolerance,
        rank_threshold=threshold,
        condition_number=condition,
        channel_ablation_stability=_channel_ablation(blocks),
        survey_axis_overlap=_survey_axis_overlap(blocks, projected),
        no_claim_reasons=tuple(dict.fromkeys(reasons)),
    )

"""Diagnostic CF4 forward-likelihood skeleton.

This module evaluates a distance-variable Gaussian diagnostic for schema-bound
CF4-like rows. It is not an evidence-grade HTT likelihood and does not promote
CF4 compact velocity products into publication-ready inference.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence

import numpy as np

from obsstat.catalogs.cf4 import Cf4Catalog

__all__ = [
    "Cf4ForwardLikelihoodResult",
    "evaluate_cf4_forward_likelihood",
]


_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_BASE_BLOCKERS = (
    "cf4_forward_catalog_not_production_bound",
    "matched_nulls_not_bound",
    "covariance_not_bound",
    "group_method_calibration_covariance_not_bound",
    "ppc_loocv_not_bound",
    "local_global_overlap_not_externally_audited",
)


def _vector(value: object, field: str, *, length: int | None = None) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{field} must be one-dimensional")
    if length is not None and array.shape[0] != length:
        raise ValueError(f"{field} must have length {length}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must contain finite values")
    return array


def _matrix(value: object, field: str, *, rows: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[0] != rows:
        raise ValueError(f"{field} must have shape ({rows}, k)")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{field} must contain finite values")
    return array


def _sha256_text(value: object, field: str) -> str:
    text = str(value).strip()
    if not _SHA256_RE.fullmatch(text):
        raise ValueError(f"{field} must be a sha256 hash")
    return text


def _input_hash_tuple(input_hashes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(input_hashes, (str, bytes)) or not input_hashes:
        raise ValueError("input_hashes must be a non-empty sequence of sha256 hashes")
    return tuple(_sha256_text(item, "input_hashes") for item in input_hashes)


def _response_rank_audit(
    *,
    local_flow_basis: np.ndarray,
    line_of_sight_unit: np.ndarray,
) -> dict[str, Any]:
    calibration_column = np.ones((local_flow_basis.shape[0], 1), dtype=float)
    design = np.column_stack((local_flow_basis, line_of_sight_unit, calibration_column))
    singular_values = np.linalg.svd(design, compute_uv=False)
    if singular_values.size:
        tolerance = float(
            max(design.shape) * np.finfo(float).eps * float(np.max(singular_values))
        )
        rank = int(np.sum(singular_values > tolerance))
    else:
        tolerance = 0.0
        rank = 0
    columns = int(design.shape[1])
    full_rank = rank == columns
    if full_rank and singular_values.size and singular_values[-1] > tolerance:
        condition_number = float(singular_values[0] / singular_values[-1])
    else:
        condition_number = float("inf")
    return {
        "rank_status": "full_rank" if full_rank else "rank_deficient",
        "design_rank": rank,
        "design_columns": columns,
        "row_count": int(design.shape[0]),
        "rank_tolerance": tolerance,
        "condition_number": condition_number,
        "local_flow_columns": int(local_flow_basis.shape[1]),
        "global_vector_columns": 3,
        "calibration_columns": 1,
    }


@dataclass(frozen=True)
class Cf4ForwardLikelihoodResult:
    """Diagnostic-only likelihood evaluation result."""

    log_likelihood: float
    chi2: float
    ndof: int
    predicted_distance_variable: np.ndarray
    residual: np.ndarray
    variance: np.ndarray
    catalog: Cf4Catalog
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    worktree_state: str
    response_rank_audit: dict[str, Any]
    blocked_reasons: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        return {
            "owner": "HTT",
            "implementation_scope": "htt",
            "claim_tier": "diagnostic_only",
            "production_status": "diagnostic_only",
            "status": "diagnostic_toy_or_schema_only",
            "log_likelihood": self.log_likelihood,
            "chi2": self.chi2,
            "ndof": self.ndof,
            "publication_ready": False,
            "native_solver_result": False,
            "transfer_source": "none",
            "score_semantics": "diagonal_diagnostic_gaussian_score",
            "sky_support_status": "cf4_object_catalog_coordinates_bound",
            "null_mock_status": "not_statistical",
            "covariance_status": "diagonal_only_no_group_method_covariance",
            "noise_model": {
                "type": "independent_diagonal_distance_variable_variance",
                "variance": "distance_uncertainty**2 + noise_variance_floor",
                "covariance_status": "diagonal_only_no_group_method_covariance",
                "group_method_calibration_covariance": "not_bound",
            },
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.worktree_state,
            "blocked_reasons": list(self.blocked_reasons),
            "response_rank_audit": dict(self.response_rank_audit),
            "catalog_metadata": self.catalog.to_metadata(),
            "distance_variable_kind": self.catalog.metadata.distance_variable_kind,
            "velocity_distribution_status": self.catalog.metadata.velocity_distribution_status,
            "velocity_gaussian_manifest_ref": self.catalog.metadata.gaussian_velocity_manifest_ref,
            "velocity_gaussian_manifest_hash": self.catalog.metadata.gaussian_velocity_manifest_hash,
            "statistics": {
                "residual_mean": float(np.mean(self.residual)),
                "residual_rms": float(np.sqrt(np.mean(self.residual**2))),
                "variance_min": float(np.min(self.variance)),
                "variance_max": float(np.max(self.variance)),
            },
            "caveats": [
                "diagonal diagnostic Gaussian score only",
                "not evidence-grade HTT inference",
                "no native low-ell solver output is used",
                "no morphology-atlas or family-selection claim is made",
                "group, method, and calibration-correlated covariance is not bound",
                "local/global response overlap is not externally audited",
            ],
        }


def evaluate_cf4_forward_likelihood(
    catalog: Cf4Catalog,
    *,
    baseline_distance_variable: Sequence[float],
    local_flow_basis: Sequence[Sequence[float]],
    local_flow_coefficients: Sequence[float],
    global_vector: Sequence[float],
    calibration_offset: float,
    config_hash: str,
    input_hashes: Sequence[str],
    generating_command: str,
    worktree_state: str,
    noise_variance_floor: float = 0.0,
) -> Cf4ForwardLikelihoodResult:
    """Evaluate a diagnostic Gaussian distance-variable likelihood."""

    n_rows = catalog.row_count
    if (
        catalog.metadata.distance_variable_kind == "peculiar_velocity"
        and not catalog.metadata.allows_exact_gaussian_velocity
    ):
        raise ValueError(
            "Gaussian velocity manifest is required before peculiar velocity "
            "variables can use exact Gaussian likelihood semantics"
        )
    baseline = _vector(
        baseline_distance_variable,
        "baseline_distance_variable",
        length=n_rows,
    )
    basis = _matrix(local_flow_basis, "local_flow_basis", rows=n_rows)
    coefficients = _vector(
        local_flow_coefficients,
        "local_flow_coefficients",
        length=basis.shape[1],
    )
    global_vec = _vector(global_vector, "global_vector", length=3)
    calibration = float(calibration_offset)
    if not np.isfinite(calibration):
        raise ValueError("calibration_offset must be finite")
    floor = float(noise_variance_floor)
    if not np.isfinite(floor) or floor < 0.0:
        raise ValueError("noise_variance_floor must be finite and non-negative")
    normalized_config_hash = _sha256_text(config_hash, "config_hash")
    normalized_input_hashes = _input_hash_tuple(input_hashes)
    command = str(generating_command).strip()
    if not command:
        raise ValueError("generating_command is required")
    state = str(worktree_state).strip()
    if not state:
        raise ValueError("worktree_state is required")

    rank_audit = _response_rank_audit(
        local_flow_basis=basis,
        line_of_sight_unit=catalog.line_of_sight_unit,
    )
    blockers = list(_BASE_BLOCKERS)
    if rank_audit["rank_status"] != "full_rank":
        blockers.append("response_rank_not_full")

    local_response = basis @ coefficients
    global_response = catalog.line_of_sight_unit @ global_vec
    predicted = baseline + local_response + global_response + calibration
    residual = catalog.distance_variable - predicted
    variance = catalog.distance_uncertainty**2 + floor
    if np.any(variance <= 0.0):
        raise ValueError("variance must be positive")
    chi2 = float(np.sum((residual**2) / variance))
    log_det = float(np.sum(np.log(2.0 * np.pi * variance)))
    log_likelihood = -0.5 * (chi2 + log_det)
    return Cf4ForwardLikelihoodResult(
        log_likelihood=float(log_likelihood),
        chi2=chi2,
        ndof=n_rows,
        predicted_distance_variable=predicted,
        residual=residual,
        variance=variance,
        catalog=catalog,
        config_hash=normalized_config_hash,
        input_hashes=normalized_input_hashes,
        generating_command=command,
        worktree_state=state,
        response_rank_audit=rank_audit,
        blocked_reasons=tuple(blockers),
    )

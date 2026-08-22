"""PR-290 synthetic Planck-lane contracts and fail-closed statistics.

This module contains no observed-data loader.  It supplies reusable typed
checks for a future common observation/null operator and an exchangeable
observation-inclusive max-scan rank that may be exercised on synthetic rows.
Unavailable numerical operators remain explicit string-valued blockers.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from typing import Sequence

import numpy as np


SCHEMA_VERSION = "htt.obsstat.planck_post275_lane.v1"


class PlanckLaneContractError(ValueError):
    """Raised when a synthetic or future Planck operator contract drifts."""


def _finite_rows(values: object) -> np.ndarray:
    try:
        rows = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlanckLaneContractError("scan rows must be numeric") from exc
    if rows.ndim != 2 or rows.shape[0] < 2 or rows.shape[1] < 1:
        raise PlanckLaneContractError(
            "scan needs one observation plus at least one null row"
        )
    if not np.all(np.isfinite(rows)):
        raise PlanckLaneContractError("scan rows must be finite")
    return rows


def _oriented_leave_one_out_scores(
    rows: np.ndarray, directions: tuple[str, ...]
) -> np.ndarray:
    n_rows, n_statistics = rows.shape
    if len(directions) != n_statistics:
        raise PlanckLaneContractError("one tail direction is required per statistic")
    scores = np.empty_like(rows)
    for column, raw_direction in enumerate(directions):
        if not isinstance(raw_direction, str):
            raise PlanckLaneContractError("tail directions must be strings")
        direction = raw_direction.lower()
        if direction == "high":
            scores[:, column] = rows[:, column]
        elif direction == "low":
            scores[:, column] = -rows[:, column]
        elif direction == "two-sided":
            values = rows[:, column]
            order = np.argsort(values, kind="mergesort")
            sorted_values = values[order]
            ranks = np.empty(n_rows, dtype=int)
            ranks[order] = np.arange(n_rows)
            remaining = n_rows - 1
            centers = np.empty(n_rows, dtype=float)
            if remaining % 2:
                middle = remaining // 2
                source = np.where(ranks <= middle, middle + 1, middle)
                centers[:] = sorted_values[source]
            else:
                upper = remaining // 2
                lower_source = np.where(ranks <= upper - 1, upper, upper - 1)
                upper_source = np.where(ranks <= upper, upper + 1, upper)
                centers[:] = (
                    sorted_values[lower_source] + sorted_values[upper_source]
                ) / 2.0
            scores[:, column] = np.abs(values - centers)
        else:
            raise PlanckLaneContractError(
                f"unsupported tail direction: {raw_direction}"
            )
    return scores


@dataclass(frozen=True)
class ObservationInclusiveMaxScan:
    observation_index: int
    local_p: tuple[Fraction, ...]
    local_p_all_rows: tuple[tuple[Fraction, ...], ...]
    observation_max_score: float
    row_max_scores: tuple[float, ...]
    global_p: Fraction
    global_exceedances_including_observation: int
    row_count: int
    statistic_count: int
    resolution_floor: Fraction

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": "htt.obsstat.observation_inclusive_max_scan.v1",
            "observation_index": self.observation_index,
            "local_p": [str(value) for value in self.local_p],
            "local_p_all_rows": [
                [str(value) for value in row] for row in self.local_p_all_rows
            ],
            "observation_max_score": self.observation_max_score,
            "row_max_scores": list(self.row_max_scores),
            "global_p": str(self.global_p),
            "global_exceedances_including_observation": (
                self.global_exceedances_including_observation
            ),
            "row_count": self.row_count,
            "null_count": self.row_count - 1,
            "statistic_count": self.statistic_count,
            "resolution_floor": str(self.resolution_floor),
            "tail_policy": "conservative_greater_or_equal",
            "scoring": "observation_inclusive_leave_one_out_per_statistic",
            "reducer": "row_wise_max_negative_log_tail_rank",
            "claim_boundary": "synthetic_or_matched_null_conditional_C2_only",
        }


def observation_inclusive_max_scan(
    rows: object,
    directions: Sequence[str],
    *,
    observation_index: int = 0,
) -> ObservationInclusiveMaxScan:
    """Return an exchangeable pooled global rank over complete scan rows.

    Every member of the observation-plus-null pool receives its own
    leave-one-out two-sided center where applicable.  Per-statistic tail ranks
    are then computed over the complete pooled score matrix, including the row
    itself, with conservative ties.  The row statistic is the maximum
    ``-log(p_local)`` (equivalently the minimum exact local rank), and the
    reported global p is the pooled rank of the selected observation row.
    """

    matrix = _finite_rows(rows)
    if (
        not isinstance(observation_index, int)
        or isinstance(observation_index, bool)
        or not 0 <= observation_index < matrix.shape[0]
    ):
        raise PlanckLaneContractError("observation_index is outside the row pool")
    oriented = _oriented_leave_one_out_scores(matrix, tuple(directions))
    n_rows, n_statistics = oriented.shape
    local_rows: list[tuple[Fraction, ...]] = []
    row_minima: list[Fraction] = []
    for row_index in range(n_rows):
        row_p = tuple(
            Fraction(
                int(
                    np.count_nonzero(oriented[:, column] >= oriented[row_index, column])
                ),
                n_rows,
            )
            for column in range(n_statistics)
        )
        local_rows.append(row_p)
        row_minima.append(min(row_p))
    observation_minimum = row_minima[observation_index]
    # A smaller minimum local rank is more extreme.  The <= comparison is the
    # conservative tie policy in this orientation and includes the observation.
    exceedances = sum(value <= observation_minimum for value in row_minima)
    global_p = Fraction(exceedances, n_rows)
    floor = Fraction(1, n_rows)
    if global_p < floor or global_p <= 0:
        raise PlanckLaneContractError("global rank fell below finite resolution")
    row_scores = tuple(-math.log(float(value)) for value in row_minima)
    return ObservationInclusiveMaxScan(
        observation_index=observation_index,
        local_p=local_rows[observation_index],
        local_p_all_rows=tuple(local_rows),
        observation_max_score=row_scores[observation_index],
        row_max_scores=row_scores,
        global_p=global_p,
        global_exceedances_including_observation=exceedances,
        row_count=n_rows,
        statistic_count=n_statistics,
        resolution_floor=floor,
    )


def validate_full_joint_covariance(
    covariance: object,
    feature_ids: Sequence[str],
) -> dict[str, object]:
    """Validate a full positive-definite covariance over a frozen feature order."""

    try:
        matrix = np.asarray(covariance, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlanckLaneContractError("covariance must be numeric") from exc
    identifiers = tuple(feature_ids)
    if (
        matrix.ndim != 2
        or matrix.shape[0] != matrix.shape[1]
        or matrix.shape[0] != len(identifiers)
        or matrix.shape[0] < 2
    ):
        raise PlanckLaneContractError(
            "covariance shape must match at least two frozen features"
        )
    if any(
        not isinstance(value, str) or not value.strip() for value in identifiers
    ) or len(set(identifiers)) != len(identifiers):
        raise PlanckLaneContractError("feature IDs must be unique non-empty strings")
    if not np.all(np.isfinite(matrix)):
        raise PlanckLaneContractError("covariance must be finite")
    if not np.allclose(matrix, matrix.T, rtol=1e-12, atol=1e-15):
        raise PlanckLaneContractError("covariance must be symmetric")
    diagonal = np.diag(np.diag(matrix))
    if np.allclose(matrix, diagonal, rtol=0.0, atol=0.0):
        raise PlanckLaneContractError("diagonal covariance shortcut is forbidden")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if float(eigenvalues[0]) <= 0.0:
        raise PlanckLaneContractError("covariance must be positive definite")
    rank = int(np.linalg.matrix_rank(matrix))
    if rank != matrix.shape[0]:
        raise PlanckLaneContractError("covariance must have full registered rank")
    return {
        "feature_ids": list(identifiers),
        "rank": rank,
        "dimension": matrix.shape[0],
        "minimum_eigenvalue": float(eigenvalues[0]),
        "maximum_eigenvalue": float(eigenvalues[-1]),
        "condition_number": float(eigenvalues[-1] / eigenvalues[0]),
        "off_diagonal_present": True,
        "status": "SYNTHETIC_FULL_COVARIANCE_CONTRACT_PASS",
        "claim_boundary": "synthetic_contract_only_not_observed_covariance",
    }


__all__ = [
    "ObservationInclusiveMaxScan",
    "PlanckLaneContractError",
    "SCHEMA_VERSION",
    "observation_inclusive_max_scan",
    "validate_full_joint_covariance",
]

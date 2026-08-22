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
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np


SCHEMA_VERSION = "htt.obsstat.planck_post275_lane.v1"
REQUIRED_COMPONENTS = ("SMICA", "Commander")
REQUIRED_MAP_PRODUCT_IDS = MappingProxyType(
    {
        "SMICA": "planck:pr3:smica:lowell:v1",
        "Commander": "planck:pr3:commander:lowell:v1",
    }
)

OPERATOR_IDENTITY_FIELDS = frozenset(
    {
        "pipeline_id",
        "map_product_id",
        "beam_id",
        "pixel_window_id",
        "mask_id",
        "mask_deconvolution_id",
        "harmonic_convention_id",
        "estimator_family_id",
        "feature_order_id",
        "covariance_id",
        "null_ensemble_id",
        "look_elsewhere_family_id",
        "response_id",
        "units_id",
    }
)


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


def require_common_operator_identity(
    observation_identity: Mapping[str, object],
    null_identity: Mapping[str, object],
) -> dict[str, object]:
    """Require one exact operator identity for observation and matched nulls."""

    if not isinstance(observation_identity, Mapping) or not isinstance(
        null_identity, Mapping
    ):
        raise PlanckLaneContractError("operator identities must be mappings")
    if (
        frozenset(observation_identity) != OPERATOR_IDENTITY_FIELDS
        or frozenset(null_identity) != OPERATOR_IDENTITY_FIELDS
    ):
        raise PlanckLaneContractError("operator identity field inventory drifted")
    for field_name in sorted(OPERATOR_IDENTITY_FIELDS):
        left = observation_identity[field_name]
        right = null_identity[field_name]
        if not isinstance(left, str) or not left.strip():
            raise PlanckLaneContractError(
                f"operator identity {field_name} must be a non-empty string"
            )
        if left != right:
            raise PlanckLaneContractError(
                "observation and null must use an identical operator identity"
            )
    return dict(observation_identity)


def require_complete_component_operator_identities(
    observation_identities: Mapping[str, Mapping[str, object]],
    null_identities: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    """Require separate, complete SMICA and Commander observation/null rows."""

    if not isinstance(observation_identities, Mapping) or not isinstance(
        null_identities, Mapping
    ):
        raise PlanckLaneContractError("component identities must be mappings")
    required = frozenset(REQUIRED_COMPONENTS)
    if (
        frozenset(observation_identities) != required
        or frozenset(null_identities) != required
    ):
        raise PlanckLaneContractError(
            "component inventory must contain exactly SMICA and Commander"
        )
    validated: dict[str, dict[str, object]] = {}
    for component in REQUIRED_COMPONENTS:
        observation = observation_identities[component]
        null = null_identities[component]
        if not isinstance(observation, Mapping) or not isinstance(null, Mapping):
            raise PlanckLaneContractError("component identity rows must be mappings")
        expected_product = REQUIRED_MAP_PRODUCT_IDS[component]
        if (
            observation.get("map_product_id") != expected_product
            or null.get("map_product_id") != expected_product
        ):
            raise PlanckLaneContractError(
                f"{component} map-product identity is not the frozen product"
            )
        validated[component] = require_common_operator_identity(observation, null)
    for field_name in sorted(OPERATOR_IDENTITY_FIELDS - {"map_product_id"}):
        if validated["SMICA"][field_name] != validated["Commander"][field_name]:
            raise PlanckLaneContractError(
                "SMICA and Commander must share the same non-product operator identity"
            )
    return validated


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


def biposh_feature_units(map_unit: str) -> dict[str, str]:
    """Return the dimensional contract induced by one temperature-map unit."""

    if not isinstance(map_unit, str) or not map_unit.strip():
        raise PlanckLaneContractError("map unit must be a non-empty string")
    if any(token in map_unit for token in ("^", "*", "/")):
        raise PlanckLaneContractError("map unit must be an atomic unit identity")
    return {
        "alm": map_unit,
        "cl": f"{map_unit}^2",
        "biposh_A": f"{map_unit}^2",
        "biposh_D": f"{map_unit}^4",
        "s_one_half": f"{map_unit}^4",
        "power_tensor": "dimensionless",
        "parity_ratio": "dimensionless",
        "axis_score": "dimensionless",
    }


def build_preactivation_capability_snapshot() -> dict[str, str]:
    """Expose unavailable PR-290 capabilities as typed, non-numeric statuses."""

    return {
        "beam_pixel_normalization": "BLOCKED_IMPLEMENTATION_UNAVAILABLE",
        "mask_deconvolution": "BLOCKED_UNDECONVOLVED",
        "multipole_vectors": "BLOCKED_EXTRACTOR_UNAVAILABLE",
        "joint_covariance": "BLOCKED_FEATURE_VECTOR_UNREGISTERED",
        "global_response": "BLOCKED_UNBOUND_GLOBAL_RESPONSE",
        "local_boost": "synthetic_operator_contract_only",
        "global_tilt": "BLOCKED_UNBOUND_GLOBAL_RESPONSE",
        "local_global_rank": "NOT_MEASURED",
        "Q": "BLOCKED_NO_DEPARTURE_BUNDLE_BUDGET",
        "F": "BLOCKED_NO_SIGN_CLEAN_XC_AND_CEILING",
        "Pi": "BLOCKED_NO_Q_OR_F_MEASURE",
        "G_F": "NOT_APPLICABLE_NO_DEPTH_AXIS",
        "likelihood_prior_posterior_evidence": "NOT_APPLICABLE_DIAGNOSTIC_ONLY",
        "observed_data": "NOT_EXECUTED",
        "public_use": "FORBIDDEN_PREACTIVATION",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }


__all__ = [
    "OPERATOR_IDENTITY_FIELDS",
    "REQUIRED_COMPONENTS",
    "REQUIRED_MAP_PRODUCT_IDS",
    "ObservationInclusiveMaxScan",
    "PlanckLaneContractError",
    "SCHEMA_VERSION",
    "biposh_feature_units",
    "build_preactivation_capability_snapshot",
    "observation_inclusive_max_scan",
    "require_complete_component_operator_identities",
    "require_common_operator_identity",
    "validate_full_joint_covariance",
]

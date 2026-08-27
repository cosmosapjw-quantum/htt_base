"""Explicit finite-pool reducers for the PMG-WU-003 map-free audit."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Sequence

import numpy as np

from obsstat.planck_post275_lane import (
    ObservationInclusiveMaxScan,
    PlanckLaneContractError,
    observation_inclusive_max_scan,
)


TAILS = ("two-sided", "upper", "lower")


def legacy_absolute_median_scan(
    rows: object,
    tails: Sequence[str],
    *,
    observation_index: int = 0,
) -> ObservationInclusiveMaxScan:
    """Expose the frozen absolute-LOO-median implementation without mutation."""

    translated = tuple(
        {"upper": "high", "lower": "low", "two-sided": "two-sided"}.get(
            str(tail).lower(), ""
        )
        for tail in tails
    )
    if "" in translated:
        raise PlanckLaneContractError("unsupported tail registry entry")
    return observation_inclusive_max_scan(
        rows, translated, observation_index=observation_index
    )


def _finite_matrix(rows: object) -> np.ndarray:
    try:
        matrix = np.asarray(rows, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlanckLaneContractError("scan rows must be numeric") from exc
    if matrix.ndim != 2 or matrix.shape[0] < 2 or matrix.shape[1] < 1:
        raise PlanckLaneContractError("scan requires at least two rows and one column")
    if not np.all(np.isfinite(matrix)):
        raise PlanckLaneContractError("scan rows must be finite")
    return matrix


def loo_ecdf_midrank_scan(
    rows: object,
    tails: Sequence[str],
    *,
    observation_index: int = 0,
) -> ObservationInclusiveMaxScan:
    """Compute the registered monotone-invariant LOO-ECDF family rank."""

    matrix = _finite_matrix(rows)
    n_rows, n_columns = matrix.shape
    if type(observation_index) is not int or not 0 <= observation_index < n_rows:
        raise PlanckLaneContractError("observation_index is outside the row pool")
    registry = tuple(str(tail).lower() for tail in tails)
    if len(registry) != n_columns or any(tail not in TAILS for tail in registry):
        raise PlanckLaneContractError("one registered tail is required per coordinate")
    # All rows share the same LOO denominator.  Retain the transformed
    # midrank numerator as an integer so mathematically tied two-sided
    # scores cannot be split by binary floating-point rounding.
    scores = np.empty(matrix.shape, dtype=np.int64)
    denominator = n_rows - 1
    for row in range(n_rows):
        others = np.delete(matrix, row, axis=0)
        less = np.count_nonzero(others < matrix[row], axis=0)
        equal = np.count_nonzero(others == matrix[row], axis=0)
        twice_midrank = 2 * less + equal
        for column, tail in enumerate(registry):
            scores[row, column] = {
                "two-sided": abs(int(twice_midrank[column]) - denominator),
                "upper": int(twice_midrank[column]),
                "lower": 2 * denominator - int(twice_midrank[column]),
            }[tail]
    local_rows: list[tuple[Fraction, ...]] = []
    minima: list[Fraction] = []
    for row in range(n_rows):
        local = tuple(
            Fraction(
                int(np.count_nonzero(scores[:, column] >= scores[row, column])),
                n_rows,
            )
            for column in range(n_columns)
        )
        local_rows.append(local)
        minima.append(min(local))
    observed_minimum = minima[observation_index]
    exceedances = sum(value <= observed_minimum for value in minima)
    global_p = Fraction(exceedances, n_rows)
    return ObservationInclusiveMaxScan(
        observation_index=observation_index,
        local_p=local_rows[observation_index],
        local_p_all_rows=tuple(local_rows),
        observation_max_score=-math.log(float(observed_minimum)),
        row_max_scores=tuple(-math.log(float(value)) for value in minima),
        global_p=global_p,
        global_exceedances_including_observation=exceedances,
        row_count=n_rows,
        statistic_count=n_columns,
        resolution_floor=Fraction(1, n_rows),
    )


__all__ = ["TAILS", "legacy_absolute_median_scan", "loo_ecdf_midrank_scan"]

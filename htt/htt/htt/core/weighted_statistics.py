"""Dependency-light weighted summaries for active HTT consumers.

These helpers are numerically identical to the historical implementations in
``htt.core.departure_posteriors``.  They live here so importing ``htt.core``
does not import the legacy scalar-projection engine or its quarantined
denominator policy.
"""
from __future__ import annotations

import numpy as np

__all__ = ["weighted_hpd", "weighted_quantile"]


def weighted_quantile(values, quantile, weights):
    """Compute a weighted quantile via sorted CDF interpolation."""

    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    idx = np.argsort(values)
    sorted_values = values[idx]
    sorted_weights = weights[idx]
    cumulative = np.cumsum(sorted_weights)
    cumulative /= cumulative[-1]
    return float(np.interp(quantile, cumulative, sorted_values))


def weighted_hpd(values, weights, level=0.68):
    """Return the shortest weighted interval containing ``level`` mass."""

    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    idx = np.argsort(values)
    sorted_values = values[idx]
    sorted_weights = weights[idx]
    sorted_weights = sorted_weights / sorted_weights.sum()
    cumulative = np.cumsum(sorted_weights)

    best_width = np.inf
    lo, hi = sorted_values[0], sorted_values[-1]
    sample_count = len(sorted_values)
    for index in range(sample_count):
        threshold = (
            cumulative[index] - sorted_weights[index] + level
        )
        if threshold > 1.0:
            break
        upper_index = np.searchsorted(cumulative, threshold)
        if upper_index >= sample_count:
            upper_index = sample_count - 1
        width = sorted_values[upper_index] - sorted_values[index]
        if width < best_width:
            best_width = width
            lo, hi = sorted_values[index], sorted_values[upper_index]
    return (float(lo), float(hi))

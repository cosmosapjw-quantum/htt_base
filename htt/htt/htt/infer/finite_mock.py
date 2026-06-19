"""Finite-mock diagnostic bounds for HTT adequacy gates."""
from __future__ import annotations

import math


def zero_trigger_upper_bound(null_count: int, confidence: float = 0.95) -> float:
    """Return the one-sided FPR upper bound for zero triggers in N mocks.

    This is a diagnostic upper bound. It must not be reported as a zero
    false-positive rate or as model evidence.
    """

    if not isinstance(null_count, int) or null_count <= 0:
        raise ValueError("null_count must be a positive integer")
    confidence_value = float(confidence)
    if not math.isfinite(confidence_value) or not 0.0 < confidence_value < 1.0:
        raise ValueError("confidence must lie in (0, 1)")
    alpha = 1.0 - confidence_value
    return 1.0 - alpha ** (1.0 / null_count)


__all__ = ["zero_trigger_upper_bound"]

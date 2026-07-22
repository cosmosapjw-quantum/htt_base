from __future__ import annotations

import numpy as np


def coherent_fraction_interval(
    observed_coherence: float,
    *,
    stochastic_baseline: tuple[float, float] = (0.42, 0.58),
    measurement_error: float = 0.03,
) -> tuple[float, float]:
    """Toy identified set for a coherent-axis fraction.

    The registered moment model is ``r = g + (1-g)b + e`` where ``g`` is the
    coherent fraction, ``b`` an unknown stochastic-alignment baseline in the
    declared interval, and ``|e| <= measurement_error``.  The function returns
    the exact grid-verified image for ``g in [0,1]``.  It is a methodology fixture,
    not a CMB physical bridge.
    """
    r = float(observed_coherence)
    if not (0 <= r <= 1):
        raise ValueError("coherence must lie in [0,1]")
    b0, b1 = map(float, stochastic_baseline)
    if not (0 <= b0 <= b1 < 1):
        raise ValueError("baseline must satisfy 0 <= b0 <= b1 < 1")
    if measurement_error < 0:
        raise ValueError("measurement_error must be non-negative")
    grid = np.linspace(0.0, 1.0, 20001)
    feasible = []
    for g in grid:
        lo = g + (1 - g) * b0 - measurement_error
        hi = g + (1 - g) * b1 + measurement_error
        if lo <= r <= hi:
            feasible.append(g)
    if not feasible:
        raise ValueError("EMPTY identified set under the declared model")
    return float(min(feasible)), float(max(feasible))

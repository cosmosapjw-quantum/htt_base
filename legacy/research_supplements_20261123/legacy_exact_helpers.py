"""Exact-source legacy helper consolidation.

Angles: input degrees, directed separation output radians (not unoriented axes).
source_zeta is the original I2/E2 convention, not independently derived physics.
Original functions are retained unchanged; parent modules are not imported.
"""
import numpy as np


def P2(mu: float) -> float:
    return 0.5 * (3.0 * mu * mu - 1.0)


def source_zeta(I2: float, E2: float) -> float:
    return 0.75 * I2 + 4.5 * E2


def _unit_vec(l_deg, b_deg):
    l, b = np.radians(l_deg), np.radians(b_deg)
    return np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])


def _angular_sep(l1, b1, l2, b2):
    d1, d2 = _unit_vec(l1, b1), _unit_vec(l2, b2)
    return np.arccos(np.clip(np.dot(d1, d2), -1, 1))

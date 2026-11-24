"""R108: the compensating tilt speed solves gamma^2 w v = |q| without cancellation for small |q|/w.

The root of v^2 + r v - 1 = 0 (r = w/|q|) was evaluated as (-r + sqrt(r^2 + 4))/2, which
loses ~eps r^2 relative accuracy (0.7%-36% at |q|/w ~ 1e-8, found by the R108 S4 BJS lane).
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from bass.background.tilted_bianchi_state import solve_compensating_tilt_velocity


@pytest.mark.parametrize("ratio", [1e-12, 1e-8, 1e-4, 0.3, 3.0, 1e4])
def test_root_satisfies_the_momentum_equation_to_rounding(ratio):
    w = 1.7
    q = np.array([0.6, -0.8, 0.0]) * ratio * w
    v = solve_compensating_tilt_velocity(q, eps_hat=1.2, p_hat=0.5)
    speed = float(np.linalg.norm(v))
    # residual of w v / (1 - v^2) = |q| evaluated exactly in rationals
    vs, ws, qs = Fraction(speed), Fraction(w), Fraction(float(np.linalg.norm(q)))
    rel = abs(float(ws * vs / (1 - vs * vs) / qs) - 1.0)
    # relative condition number of v -> w v / (1 - v^2) is (1 + v^2) / (1 - v^2)
    cond = (1.0 + speed * speed) / (1.0 - speed * speed)
    assert rel < 4e-16 * cond, (ratio, rel, cond)
    assert np.allclose(v / speed, q / np.linalg.norm(q), rtol=0, atol=1e-15)


def test_small_momentum_limit_is_q_over_w():
    v = solve_compensating_tilt_velocity(np.array([0.0, 0.0, 3e-9]), eps_hat=1.0, p_hat=0.0)
    assert abs(v[2] / 3e-9 - 1.0) < 1e-15

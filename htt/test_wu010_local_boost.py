from __future__ import annotations

import numpy as np
import pytest

from obsstat.boost_response import (
    boost_response_metric,
    contract_octupole_with_quadrupole,
    quadrupole_boost_octupole,
)
from obsstat.lorentz_sky_pullback import (
    aberrate_sky_direction,
    deaberrate_sky_direction,
)

pytestmark = pytest.mark.fast


def test_wu010_aberration_round_trip() -> None:
    directions = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    beta = np.array([0.012, -0.021, 0.015])
    boosted = aberrate_sky_direction(directions, beta)
    restored = deaberrate_sky_direction(boosted, beta)
    np.testing.assert_allclose(restored, directions, atol=3e-14, rtol=0.0)


def test_wu010_quadrupole_response_contraction_identity() -> None:
    q = np.array(
        [[0.8, -0.3, 0.2], [-0.3, -0.5, 0.4], [0.2, 0.4, -0.3]],
        dtype=float,
    )
    beta = np.array([0.02, -0.01, 0.03])
    octupole = quadrupole_boost_octupole(q, beta)
    np.testing.assert_allclose(
        contract_octupole_with_quadrupole(octupole, q),
        boost_response_metric(q) @ beta,
        atol=3e-15,
        rtol=0.0,
    )

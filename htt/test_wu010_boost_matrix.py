from __future__ import annotations

import numpy as np
import pytest

from obsstat.boost_response import (
    boost_response_matrix,
    boost_response_metric,
    stf3_component_metric,
)

pytestmark = pytest.mark.fast


def test_wu010_component_response_has_rank_three_and_exact_gram() -> None:
    q = np.array(
        [[0.8, -0.3, 0.2], [-0.3, -0.5, 0.4], [0.2, 0.4, -0.3]],
        dtype=float,
    )
    response = boost_response_matrix(q)
    assert response.shape == (7, 3)
    assert np.linalg.matrix_rank(response, tol=1.0e-13) == 3
    np.testing.assert_allclose(
        response.T @ stf3_component_metric() @ response,
        3.0 * boost_response_metric(q),
        atol=2.0e-14,
        rtol=0.0,
    )

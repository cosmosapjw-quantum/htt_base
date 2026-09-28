from __future__ import annotations

import numpy as np
import pytest

from obsstat import processed_boost_error_envelope as api


def test_exact_zero_family_is_rejected_as_semantically_empty() -> None:
    active = np.zeros((1, 2, 2), dtype=np.float64)
    active[0] = np.eye(2)
    zero = np.zeros((3, 2, 2), dtype=np.float64)

    with pytest.raises(api.MatrixErrorEnvelopeError, match="identically zero"):
        api.build_output_error_envelope(
            {"active": active, "zero": zero},
            family_radii={"active": 1.0, "zero": 7.0},
            reference_operator_norm=1.0,
        )

    with pytest.raises(api.MatrixErrorEnvelopeError, match="identically zero"):
        api.build_output_error_envelope(
            {"zero": zero},
            family_radii={"zero": 1.0},
            reference_operator_norm=1.0,
        )

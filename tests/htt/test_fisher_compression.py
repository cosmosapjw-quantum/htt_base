import numpy as np
import pytest

from htt.infer.fisher_compression import gaussian_covariance_fisher_full_and_diag


def test_off_diagonal_covariance_derivative_has_full_but_no_diagonal_information():
    derivative = np.array([[0.0, 1.0], [1.0, 0.0]])

    audit = gaussian_covariance_fisher_full_and_diag([derivative])

    assert audit.owner == "HTT"
    assert audit.claim_tier == "diagnostic_only"
    assert audit.full_fisher[0, 0] == pytest.approx(1.0)
    assert audit.diagonal_fisher[0, 0] == pytest.approx(0.0)
    assert audit.information_loss[0, 0] == pytest.approx(1.0)
    assert audit.diagonal_compression_loses_information is True


def test_fisher_audit_rejects_non_square_derivatives():
    with pytest.raises(ValueError, match="square"):
        gaussian_covariance_fisher_full_and_diag([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]])

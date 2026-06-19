import pytest

from htt.infer.finite_mock import zero_trigger_upper_bound


def test_zero_trigger_bound_for_100_is_not_zero():
    assert zero_trigger_upper_bound(100, 0.95) == pytest.approx(
        1 - 0.05 ** (1 / 100)
    )
    assert zero_trigger_upper_bound(100, 0.95) > 0.0


def test_zero_trigger_bound_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="null_count"):
        zero_trigger_upper_bound(0)
    with pytest.raises(ValueError, match="confidence"):
        zero_trigger_upper_bound(10, 1.0)

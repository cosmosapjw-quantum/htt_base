import numpy as np
import pytest
from mio.formalism.physical_pushforward import ratio_pushforward


def test_legacy_ratio_finite_semantics_remain_available():
    result = ratio_pushforward('ratio', np.array([1., 4.]), np.array([1., 2.]), 'legacy_ratio')
    assert result.status == 'OK'


@pytest.mark.parametrize('value', [np.nan, np.inf, -np.inf])
def test_nonfinite_ratio_is_never_ok(value):
    assert ratio_pushforward('ratio', [value], [1.], 'legacy_ratio').status == 'BLOCKED_NONFINITE_TRANSFORM'
    assert ratio_pushforward('ratio', [1.], [value], 'legacy_ratio').status == 'BLOCKED_NONFINITE_TRANSFORM'


def test_overflow_and_invalid_guard_are_explicit():
    assert ratio_pushforward('ratio', [1e308], [1e-308], 'legacy_ratio', zero_guard=0).status == 'BLOCKED_NONFINITE_TRANSFORM'
    assert ratio_pushforward('ratio', [1.], [0.], 'legacy_ratio').status == 'BLOCKED_ZERO_DENOMINATOR_BRANCH'
    for guard in [-1, np.nan, np.inf]:
        with pytest.raises(ValueError):
            ratio_pushforward('ratio', [1.], [1.], 'legacy_ratio', zero_guard=guard)

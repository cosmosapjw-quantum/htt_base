from __future__ import annotations

import pytest

from bass.inference import bayes_factor, run_posterior


@pytest.mark.skip(reason="pending FB-11.5 implementation — skeleton only")
def test_fb115_synthetic_injection_coverage_contract() -> None:
    nominal_coverage = 0.68
    tolerance = 0.05

    assert callable(run_posterior)
    assert callable(bayes_factor)
    assert nominal_coverage == 0.68
    assert tolerance == 0.05
